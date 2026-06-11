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
