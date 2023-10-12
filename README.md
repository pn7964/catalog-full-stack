# Item Catalog Application

This is a web application that provides a list of items within a variety of categories and integrate third party user registration and authentication. Authenticated users should have the ability to post, edit, and delete their own items.

## Prerequisite
In Linux machine python installed

## Getting Started

Extract the CatalogProject.zip file into a folder. It will have following important files.
* project.py  - It contains Server code
* database_setup.py - Tbales and ORM mapping
* lotsofitems.py - Intial data load
* client_secrets.json - Google Authentication deatils
* fb_client_secrets.json - Facebook Authentication deatils
* README.md  
* Report_Output.docx  - Screen shots of the tool working

Below are the steps to run the tool

### Update authentication details ###
Update fb_client_secrets.json with your details
```
{
  "web": {
    "app_id": "YOUR APP ID",
    "app_secret": "YOUR APP SECRET CODE"
  }
}
```

Update client_secrets.json with your details
```
"client_secret":"v21ojg_XfhJl4Z_kHVt1FTht"
"client_id":"YOUR CLIENT_ID"
```

For Facebook login one more update required in static/login.html
```
<script>
  window.fbAsyncInit = function() {
  FB.init({
    appId      : 'YOUR FB APP ID HERE',
    cookie     : true,  // enable cookies to allow the server to access
                        // the session
    xfbml      : true,  // parse social plugins on this page
    version    : 'v4.0' // use version 4.0
  });

  };
```

### Database Setup ###
Set up the database using below command
```
python database_setup.py
```

### Data Set up ###
Run below command to load initial data
```
python  lotsofitems.py
```

### Start the server ###
Run below command to start the server
```
python project.py 
```

### Open the application ###
Open the below URL in browser
```
http://localhost:5000/
```

### API can be accessed from 
API can be accessed from below URL, It returns JSON object of all Categories and Items
```
http://localhost:5000/catalog/JSON
```
Application page will be displayed. ItemCatalog_Manual.docx has more details.

### Report sample
Sample screenshots can be found in Report_Output.docx 
