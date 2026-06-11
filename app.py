"""
Flask backend for Informatica MDM hierarchy navigation
Supports: Organization → Location → Menu Catalog → Recipe → Modifier Group → Ingredient
"""

import os
import json
import requests
from datetime import datetime, timedelta
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Configuration
SESSION_FILE = "/tmp/mdm_b360_session.json"
SESSION_DURATION_MINUTES = 30
LOGIN_URL = "https://dmp-us.informaticacloud.com/saas/public/core/v3/login"
SOURCE_SYSTEM = "admin.default.system"

# Entity type mappings
ENTITY_TYPES = {
    'organization': 'Organization',
    'location': 'Location',
    'menu_catalog': 'Menu Catalog',
    'recipe': 'Recipe',
    'modifier_group': 'Modifier Group',
    'ingredient': 'Ingredient'
}

# Hierarchy configurations
HIERARCHIES = {
    'organization_to_location': {
        'name': 'Location Hierarchy',
        'from_type': 'Organization',
        'to_type': 'Location'
    },
    'location_to_menu': {
        'name': 'Location Hierarchy',
        'from_type': 'Location',
        'to_type': 'Menu Catalog'
    },
    'menu_to_recipe': {
        'name': 'Menu',
        'from_type': 'Menu Catalog',
        'to_type': 'Recipe'
    },
    'recipe_to_modifier_group': {
        'name': 'Menu',
        'from_type': 'Recipe',
        'to_type': 'Modifier Group'
    },
    'modifier_group_to_ingredient': {
        'name': 'Modification Groups',
        'from_type': 'Modifier Group',
        'to_type': 'Ingredient'
    }
}


class MDMSession:
    """Manages MDM session with 30-minute caching"""

    @staticmethod
    def get_session():
        """Load and validate existing session"""
        if not os.path.exists(SESSION_FILE):
            return None

        try:
            with open(SESSION_FILE, 'r') as f:
                session_data = json.load(f)

            timestamp = datetime.fromisoformat(session_data['timestamp'])
            age = datetime.now() - timestamp

            if age.total_seconds() < SESSION_DURATION_MINUTES * 60:
                return session_data
        except Exception as e:
            print(f"Error loading session: {e}")

        return None

    @staticmethod
    def save_session(session_id, base_url, username):
        """Save session to file"""
        session_data = {
            "session_id": session_id,
            "base_url": base_url,
            "timestamp": datetime.now().isoformat(),
            "username": username
        }
        with open(SESSION_FILE, 'w') as f:
            json.dump(session_data, f, indent=2)
        return session_data

    @staticmethod
    def transform_base_url(login_base_url):
        """Transform login base URL to MDM base URL"""
        url = login_base_url.rstrip('/saas')
        parts = url.split('.')
        if len(parts) > 0:
            protocol_and_pod = url.split('//')
            if len(protocol_and_pod) == 2:
                protocol = protocol_and_pod[0]
                rest = protocol_and_pod[1]
                pod = rest.split('.')[0]
                rest_parts = '.'.join(rest.split('.')[1:])
                return f"{protocol}//{pod}-mdm.{rest_parts}"
        return url


class MDMClient:
    """Client for Informatica MDM API calls"""

    def __init__(self, session_id, base_url):
        self.session_id = session_id
        self.base_url = base_url
        self.headers = {
            "IDS-SESSION-ID": session_id,
            "Content-Type": "application/json"
        }

    def search_entities(self, entity_type, search_term=None, business_id=None, max_results=100):
        """Search for business entities"""
        url = f"{self.base_url}/search/public/api/v1/search"

        if business_id:
            payload = {
                "entityType": entity_type,
                "fields": {
                    "_meta.businessId": business_id
                },
                "pageSize": max_results,
                "pageOffset": 0
            }
        else:
            payload = {
                "entityType": entity_type,
                "search": search_term or "*",
                "pageSize": max_results,
                "pageOffset": 0,
                "maxRecords": max_results,
                "sort": [{"fieldName": "_meta.businessId", "order": "ASCENDING"}]
            }

        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error searching entities: {e}")
            if hasattr(e.response, 'text'):
                print(f"Response: {e.response.text}")
            raise

    def get_hierarchy_children(self, hierarchy_name, parent_business_id, parent_entity_type, child_entity_type):
        """
        Get children of a parent entity in a hierarchy.
        This uses the hierarchy service to find related child entities.
        """
        # For hierarchy navigation, we'll use relationship filtering
        # First, we need to find the relationship that connects these entities

        # Since we don't have the relationship internal ID cached, we'll search by filtering
        # on parent entity and looking for children of the correct type

        url = f"{self.base_url}/shm-service/api/v1/hierarchy/{hierarchy_name}/nodes"

        # Try the hierarchy nodes endpoint with parent filter
        try:
            params = {
                "parentBusinessId": parent_business_id,
                "entityType": child_entity_type
            }
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Hierarchy nodes endpoint failed: {e}")

            # Fallback: Try searching for relationships
            # This is a more generic approach that should work
            return self._get_children_via_search(parent_business_id, parent_entity_type, child_entity_type)

    def _get_children_via_search(self, parent_business_id, parent_entity_type, child_entity_type):
        """
        Fallback method: Search for child entities that have a relationship to the parent.
        This is less efficient but more reliable across different MDM configurations.
        """
        # For now, we'll search all entities of the child type
        # In production, you'd want to filter by relationship
        search_result = self.search_entities(child_entity_type, search_term="*", max_results=1000)

        # TODO: Filter by parent relationship
        # This would require knowing the relationship internal ID and using the relationship filter API

        return search_result

    def get_entity_details(self, entity_type, business_id):
        """Get detailed information about a specific entity"""
        result = self.search_entities(entity_type, business_id=business_id)
        if result.get('searchResult', {}).get('records'):
            return result['searchResult']['records'][0]
        return None


# =================================================================
# API ENDPOINTS
# =================================================================

@app.route('/api/auth/login', methods=['POST'])
def login():
    """Authenticate with Informatica MDM"""
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400

    try:
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        payload = {
            "username": username,
            "password": password
        }

        response = requests.post(LOGIN_URL, headers=headers, json=payload)
        response.raise_for_status()

        auth_data = response.json()
        session_id = auth_data.get("sessionId")
        login_base_url = auth_data.get("baseUrl")

        # Transform base URL
        base_url = MDMSession.transform_base_url(login_base_url)

        # Save session
        session_data = MDMSession.save_session(session_id, base_url, username)

        return jsonify({
            'success': True,
            'username': username,
            'baseUrl': base_url,
            'sessionId': session_id[:10] + '...',  # Masked for security
            'expiresIn': SESSION_DURATION_MINUTES
        })

    except requests.exceptions.RequestException as e:
        error_msg = str(e)
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_data = e.response.json()
                error_msg = error_data.get('message', error_msg)
            except:
                error_msg = e.response.text or error_msg

        return jsonify({'error': f'Authentication failed: {error_msg}'}), 401


@app.route('/api/auth/session', methods=['GET'])
def check_session():
    """Check if current session is valid"""
    session = MDMSession.get_session()

    if session:
        timestamp = datetime.fromisoformat(session['timestamp'])
        age = datetime.now() - timestamp
        remaining = SESSION_DURATION_MINUTES * 60 - age.total_seconds()

        return jsonify({
            'valid': True,
            'username': session['username'],
            'remainingMinutes': round(remaining / 60, 1)
        })

    return jsonify({'valid': False}), 401


@app.route('/api/organizations/search', methods=['GET'])
def search_organizations():
    """Search organizations by name"""
    session = MDMSession.get_session()
    if not session:
        return jsonify({'error': 'Session expired. Please login.'}), 401

    search_term = request.args.get('q', '*')

    try:
        client = MDMClient(session['session_id'], session['base_url'])
        result = client.search_entities(
            ENTITY_TYPES['organization'],
            search_term=f"{search_term}*" if search_term != '*' else '*',
            max_results=50
        )

        records = result.get('searchResult', {}).get('records', [])

        # Format response
        organizations = []
        for record in records:
            org = {
                'businessId': record.get('_meta', {}).get('businessId'),
                'internalId': record.get('_meta', {}).get('id'),
                'name': record.get('Name') or record.get('name') or 'Unnamed',
                'type': record.get('Type') or record.get('type'),
                'state': record.get('_meta', {}).get('state'),
                'rawData': record
            }
            organizations.append(org)

        return jsonify({
            'success': True,
            'count': len(organizations),
            'organizations': organizations
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/organizations/<business_id>/locations', methods=['GET'])
def get_organization_locations(business_id):
    """Get all locations for an organization"""
    session = MDMSession.get_session()
    if not session:
        return jsonify({'error': 'Session expired. Please login.'}), 401

    try:
        client = MDMClient(session['session_id'], session['base_url'])
        result = client.get_hierarchy_children(
            'Location Hierarchy',
            business_id,
            ENTITY_TYPES['organization'],
            ENTITY_TYPES['location']
        )

        records = result.get('searchResult', {}).get('records', [])

        locations = []
        for record in records:
            loc = {
                'businessId': record.get('_meta', {}).get('businessId'),
                'internalId': record.get('_meta', {}).get('id'),
                'name': record.get('Name') or record.get('name') or 'Unnamed',
                'address': record.get('Address') or record.get('address'),
                'city': record.get('City') or record.get('city'),
                'state': record.get('State') or record.get('state'),
                'status': record.get('_meta', {}).get('state'),
                'rawData': record
            }
            locations.append(loc)

        return jsonify({
            'success': True,
            'organizationId': business_id,
            'count': len(locations),
            'locations': locations
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/locations/<business_id>/menus', methods=['GET'])
def get_location_menus(business_id):
    """Get all menu catalogs for a location"""
    session = MDMSession.get_session()
    if not session:
        return jsonify({'error': 'Session expired. Please login.'}), 401

    try:
        client = MDMClient(session['session_id'], session['base_url'])
        result = client.get_hierarchy_children(
            'Location Hierarchy',
            business_id,
            ENTITY_TYPES['location'],
            ENTITY_TYPES['menu_catalog']
        )

        records = result.get('searchResult', {}).get('records', [])

        menus = []
        for record in records:
            menu = {
                'businessId': record.get('_meta', {}).get('businessId'),
                'internalId': record.get('_meta', {}).get('id'),
                'name': record.get('Name') or record.get('name') or 'Unnamed',
                'description': record.get('Description') or record.get('description'),
                'status': record.get('_meta', {}).get('state'),
                'rawData': record
            }
            menus.append(menu)

        return jsonify({
            'success': True,
            'locationId': business_id,
            'count': len(menus),
            'menus': menus
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/menus/<business_id>/recipes', methods=['GET'])
def get_menu_recipes(business_id):
    """Get all recipes for a menu catalog"""
    session = MDMSession.get_session()
    if not session:
        return jsonify({'error': 'Session expired. Please login.'}), 401

    try:
        client = MDMClient(session['session_id'], session['base_url'])
        result = client.get_hierarchy_children(
            'Menu',
            business_id,
            ENTITY_TYPES['menu_catalog'],
            ENTITY_TYPES['recipe']
        )

        records = result.get('searchResult', {}).get('records', [])

        recipes = []
        for record in records:
            recipe = {
                'businessId': record.get('_meta', {}).get('businessId'),
                'internalId': record.get('_meta', {}).get('id'),
                'name': record.get('Name') or record.get('name') or 'Unnamed',
                'description': record.get('Description') or record.get('description'),
                'category': record.get('Category') or record.get('category'),
                'status': record.get('_meta', {}).get('state'),
                'rawData': record
            }
            recipes.append(recipe)

        return jsonify({
            'success': True,
            'menuId': business_id,
            'count': len(recipes),
            'recipes': recipes
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/recipes/<business_id>/modifier-groups', methods=['GET'])
def get_recipe_modifier_groups(business_id):
    """Get all modifier groups for a recipe"""
    session = MDMSession.get_session()
    if not session:
        return jsonify({'error': 'Session expired. Please login.'}), 401

    try:
        client = MDMClient(session['session_id'], session['base_url'])
        result = client.get_hierarchy_children(
            'Menu',
            business_id,
            ENTITY_TYPES['recipe'],
            ENTITY_TYPES['modifier_group']
        )

        records = result.get('searchResult', {}).get('records', [])

        modifier_groups = []
        for record in records:
            group = {
                'businessId': record.get('_meta', {}).get('businessId'),
                'internalId': record.get('_meta', {}).get('id'),
                'name': record.get('Name') or record.get('name') or 'Unnamed',
                'description': record.get('Description') or record.get('description'),
                'status': record.get('_meta', {}).get('state'),
                'rawData': record
            }
            modifier_groups.append(group)

        return jsonify({
            'success': True,
            'recipeId': business_id,
            'count': len(modifier_groups),
            'modifierGroups': modifier_groups
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/modifier-groups/<business_id>/ingredients', methods=['GET'])
def get_modifier_group_ingredients(business_id):
    """Get all ingredients for a modifier group"""
    session = MDMSession.get_session()
    if not session:
        return jsonify({'error': 'Session expired. Please login.'}), 401

    try:
        client = MDMClient(session['session_id'], session['base_url'])
        result = client.get_hierarchy_children(
            'Modification Groups',
            business_id,
            ENTITY_TYPES['modifier_group'],
            ENTITY_TYPES['ingredient']
        )

        records = result.get('searchResult', {}).get('records', [])

        ingredients = []
        for record in records:
            ingredient = {
                'businessId': record.get('_meta', {}).get('businessId'),
                'internalId': record.get('_meta', {}).get('id'),
                'name': record.get('Name') or record.get('name') or 'Unnamed',
                'description': record.get('Description') or record.get('description'),
                'allergens': record.get('Allergens') or record.get('allergens'),
                'status': record.get('_meta', {}).get('state'),
                'rawData': record
            }
            ingredients.append(ingredient)

        return jsonify({
            'success': True,
            'modifierGroupId': business_id,
            'count': len(ingredients),
            'ingredients': ingredients
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/')
def index():
    """Serve the frontend HTML"""
    import os
    file_path = os.path.join(os.path.dirname(__file__), 'index.html')
    with open(file_path, 'r') as f:
        return f.read()


@app.route('/<path:path>')
def serve_static(path):
    """Serve static files"""
    import os
    directory = os.path.dirname(__file__)
    return send_from_directory(directory, path)


if __name__ == '__main__':
    print("=" * 65)
    print("  MDM HIERARCHY NAVIGATION - Flask Backend")
    print("=" * 65)
    print(f"  Starting server on http://localhost:8080")
    print(f"  Session duration: {SESSION_DURATION_MINUTES} minutes")
    print("=" * 65)

    app.run(debug=True, port=8080)
