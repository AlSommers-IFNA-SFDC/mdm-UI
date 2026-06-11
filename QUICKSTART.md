# Quick Start Guide - MDM Hierarchy Navigator

## 🚀 Get Started in 3 Steps

### Step 1: Clone the Repository
```bash
git clone https://github.com/AlSommers-IFNA-SFDC/mdm-UI.git
cd mdm-UI
```

### Step 2: Install Dependencies (if needed)
```bash
pip3 install -r requirements.txt
```

### Step 3: Start the Server
```bash
./start.sh
```

Or run directly:
```bash
python3 app.py
```

### Step 4: Open in Browser
Navigate to: **http://localhost:8080**

---

## 🔐 First Time Login

1. Enter your Informatica MDM credentials
2. Session will be cached for 30 minutes
3. You'll see the main navigation interface

---

## 🗺️ Navigation Flow

```
1. Search Organization (e.g., "Dine Brands")
   ↓
2. Select Organization → View Locations
   ↓
3. Select Location → View Menu Catalogs
   ↓
4. Select Menu → View Recipes
   ↓
5. Select Recipe → View Modifier Groups
   ↓
6. Select Modifier Group → View Ingredients
```

---

## 💡 Tips

- **Search**: Type 2+ characters to start searching organizations
- **Breadcrumbs**: Click any breadcrumb item to jump back up the hierarchy
- **Session**: Your login session expires after 30 minutes - just login again
- **Refresh**: If data doesn't load, check that hierarchies are configured in MDM:
  - "Location Hierarchy" (Organization → Location → Menu Catalog)
  - "Menu" (Menu Catalog → Recipe → Modifier Group)
  - "Modification Groups" (Modifier Group → Ingredient)

---

## 🛠️ Configuration

Edit these values in `app.py` if needed:

```python
LOGIN_URL = "https://dmp-us.informaticacloud.com/saas/public/core/v3/login"
SOURCE_SYSTEM = "admin.default.system"
SESSION_DURATION_MINUTES = 30
```

---

## 📋 Entity Types

The UI navigates these MDM entity types:
- **Organization** - Top-level franchiser/company
- **Location** - Store/restaurant locations
- **Menu Catalog** - Menu offerings per location
- **Recipe** - Individual menu items
- **Modifier Group** - Customization groups (e.g., "Toppings", "Sizes")
- **Ingredient** - Individual ingredients/components

---

## 🐛 Troubleshooting

**Port 8080 already in use?**
```bash
# Kill existing process
lsof -ti:8080 | xargs kill -9

# Or change port in app.py (line ~560):
app.run(debug=True, port=8081)
```

**Connection refused?**
- Check if the MDM login URL is correct
- Verify your network can reach the MDM instance
- Confirm your credentials are valid

**Empty results?**
- Verify hierarchies exist in MDM with correct names
- Check that relationships are loaded between entities
- Try searching for a different organization

**Session expired?**
- Click logout and login again
- Sessions automatically expire after 30 minutes

---

## 📚 Full Documentation

See [README.md](README.md) for complete documentation including:
- API endpoints
- Architecture details
- Configuration options
- Development notes
