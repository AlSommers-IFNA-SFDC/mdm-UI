# MDM Hierarchy Navigator

A Flask-based web interface for navigating Informatica MDM hierarchies.

## Features

- **Organization Search**: Search and select organizations by name
- **Location Navigation**: View all locations under an organization (Location Hierarchy)
- **Menu Catalog Browsing**: See menu catalogs associated with a location (Location Hierarchy)
- **Recipe Listing**: Browse recipes within a menu catalog (Menu hierarchy)
- **Modifier Group Details**: View modifier groups for each recipe (Menu hierarchy)
- **Ingredient Discovery**: See all ingredients in a modifier group (Modification Groups hierarchy)

## Entity Hierarchy

```
Organization
└── Location (Hierarchy: "Location Hierarchy")
    └── Menu Catalog (Hierarchy: "Location Hierarchy")
        └── Recipe (Hierarchy: "Menu")
            └── Modifier Group (Hierarchy: "Menu")
                └── Ingredient (Hierarchy: "Modification Groups")
```

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Run the Flask application:
```bash
python app.py
```

3. Open your browser to: http://localhost:8080

## Usage

1. **Login**: Enter your Informatica MDM credentials
   - Sessions are cached for 30 minutes
   - Sessions automatically refresh

2. **Search Organizations**: Type in the search box to find organizations
   - Wildcard search supported (auto-appends *)
   - Results update as you type

3. **Navigate the Hierarchy**:
   - Click an organization to see its locations
   - Click a location to see its menu catalogs
   - Click a menu catalog to see recipes
   - Click a recipe to see modifier groups
   - Click a modifier group to see ingredients

4. **Breadcrumb Navigation**: Click any item in the breadcrumb to jump back to that level

## API Endpoints

### Authentication
- `POST /api/auth/login` - Login with username/password
- `GET /api/auth/session` - Check current session status

### Hierarchy Navigation
- `GET /api/organizations/search?q=<term>` - Search organizations
- `GET /api/organizations/<id>/locations` - Get locations for organization
- `GET /api/locations/<id>/menus` - Get menu catalogs for location
- `GET /api/menus/<id>/recipes` - Get recipes for menu catalog
- `GET /api/recipes/<id>/modifier-groups` - Get modifier groups for recipe
- `GET /api/modifier-groups/<id>/ingredients` - Get ingredients for modifier group

## Configuration

Edit `app.py` to customize:
- `SOURCE_SYSTEM`: Default is "admin.default.system"
- `SESSION_DURATION_MINUTES`: Session cache duration (default: 30)
- `LOGIN_URL`: Informatica MDM login endpoint

## Architecture

**Backend (Flask)**:
- Session management with file-based caching
- MDM API client for search and hierarchy navigation
- RESTful API endpoints for frontend consumption

**Frontend (HTML/CSS/JS)**:
- Single-page application with vanilla JavaScript
- Responsive grid layout for hierarchy levels
- Real-time search with debouncing
- Breadcrumb navigation for quick traversal

## Notes

- The hierarchy navigation currently uses a fallback method (searching all entities) because the direct hierarchy API endpoints may require additional configuration in your MDM instance
- For production use, you should implement proper relationship-based hierarchy traversal using relationship internal IDs
- Session tokens expire after 30 minutes of inactivity
- All API calls use the `IDS-SESSION-ID` header for authentication

## Troubleshooting

**"Session expired" errors**: 
- Re-login to obtain a new session token

**Empty results at hierarchy levels**:
- Verify that relationships and hierarchies are properly configured in MDM
- Check that the hierarchy names match exactly: "Location Hierarchy", "Menu", "Modification Groups"
- Ensure entities have been properly loaded with relationships

**Connection errors**:
- Verify the MDM login URL is correct
- Check that your MDM instance is accessible
- Confirm credentials are correct


## app.py documentation
 Here's a breakdown of where different API calls are located in app.py:

  🔧 API Call Locations in app.py

  Authentication API (lines ~213-250)

  @app.route('/api/auth/login', methods=['POST'])
  def login():
      # Makes POST to: LOGIN_URL (line 19)
      # Currently: https://dmp-us.informaticacloud.com/saas/public/core/v3/login

  MDM Search API (lines ~125-156)

  class MDMClient:
      def search_entities(self, entity_type, search_term=None, business_id=None):
          # Makes POST to: {base_url}/search/public/api/v1/search

  Hierarchy Navigation API (lines ~158-199)

  def get_hierarchy_children(self, hierarchy_name, parent_business_id, ...):
      # Makes GET to: {base_url}/shm-service/api/v1/hierarchy/{hierarchy_name}/nodes
      # Fallback uses search if hierarchy endpoint fails

  Flask Route Endpoints (lines ~280-420)

  All these call the MDMClient methods above:
  - /api/organizations/search (line ~280)
  - /api/organizations/<id>/locations (line ~320)
  - /api/locations/<id>/menus (line ~355)
  - /api/menus/<id>/recipes (line ~390)
  - /api/recipes/<id>/modifier-groups (line ~425)
  - /api/modifier-groups/<id>/ingredients (line ~460)
  
  📝 Common Updates You Might Need

  Change API Base URL

  Line 19:
  LOGIN_URL = "https://dmp-us.informaticacloud.com/saas/public/core/v3/login"
  
  Change Source System

  Line 20:
  SOURCE_SYSTEM = "admin.default.system"
  
  Update Entity Type Names

  Lines 23-30:
  ENTITY_TYPES = {
      'organization': 'Organization',
      'location': 'Location',
      'menu_catalog': 'Menu Catalog',
      # etc...
  }   
  
  Update Hierarchy Names

  Lines 33-59:
  HIERARCHIES = {
      'organization_to_location': {
          'name': 'Location Hierarchy',  # ← Change if different in MDM
          ...
      }   
  }

  Modify Search Parameters

  Lines ~139-146: Adjust pageSize, maxRecords, sorting, etc.

  Add Custom Headers or Authentication

  Lines ~120-123: Modify the headers dict in MDMClient.__init__

  ---
  Pro tip: After making changes to app.py, restart the Flask server:
  # Stop current server (Ctrl+C)
  # Then restart:
  ./start.sh
  
  The index.html file only contains the frontend UI and doesn't make direct API calls - it calls your Flask backend
  endpoints which then call MDM.
