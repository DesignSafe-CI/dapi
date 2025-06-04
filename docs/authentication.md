# Authentication

This guide explains how to authenticate with DesignSafe using the dapi library. Authentication is required to access DesignSafe resources and submit jobs.

## 🔐 Overview

dapi uses your DesignSafe credentials to authenticate with the TAPIS v3 API. The library supports multiple methods for providing credentials, following a secure credential resolution hierarchy.

## 🏆 Credential Resolution Hierarchy

dapi looks for credentials in the following order:

1. **Explicit parameters** passed to `DSClient()`
2. **Environment variables** (`DESIGNSAFE_USERNAME`, `DESIGNSAFE_PASSWORD`)
3. **`.env` file** in your project directory
4. **Interactive prompts** for missing credentials

## 🔑 Authentication Methods

### Method 1: Environment Variables (Recommended)

Set environment variables in your shell:

```bash
export DESIGNSAFE_USERNAME="your_username"
export DESIGNSAFE_PASSWORD="your_password"
```

Then initialize the client:

```python
from dapi import DSClient

# Automatically uses environment variables
client = DSClient()
```

#### Persistent Environment Variables

Add to your shell configuration file (`~/.bashrc`, `~/.zshrc`, etc.):

```bash
# Add these lines to your shell config
export DESIGNSAFE_USERNAME="your_username"
export DESIGNSAFE_PASSWORD="your_password"
```

### Method 2: .env File (Recommended for Projects)

Create a `.env` file in your project root:

```bash
# .env file
DESIGNSAFE_USERNAME=your_username
DESIGNSAFE_PASSWORD=your_password
```

!!! warning "Security Note"
    Never commit `.env` files to version control. Add `.env` to your `.gitignore` file.

Initialize the client:

```python
from dapi import DSClient

# Automatically loads from .env file
client = DSClient()

# Or specify a custom .env file path
client = DSClient(env_file="path/to/custom.env")
```

### Method 3: Interactive Prompts

If no credentials are found, dapi will prompt you:

```python
from dapi import DSClient

client = DSClient()
# Output:
# Enter DesignSafe Username: your_username
# Enter DesignSafe Password: [hidden input]
# Authentication successful.
```

### Method 4: Explicit Parameters

Pass credentials directly (not recommended for production):

```python
from dapi import DSClient

client = DSClient(
    username="your_username",
    password="your_password"
)
```

## 🔒 Security Best Practices

### 1. Use Environment Variables or .env Files
```python
# ✅ Good - uses environment variables
client = DSClient()

# ❌ Avoid - credentials in code
client = DSClient(username="user", password="pass")
```

### 2. Protect Your .env File
```bash
# Add to .gitignore
echo ".env" >> .gitignore

# Set restrictive permissions (Unix/Linux/macOS)
chmod 600 .env
```

### 3. Use Strong Passwords
- Use your DesignSafe account password
- Enable two-factor authentication on your DesignSafe account

### 4. Rotate Credentials Regularly
- Change your DesignSafe password periodically
- Update stored credentials when changed

## 🏗️ DesignSafe Jupyter Environment

### Setting Environment Variables in Jupyter

```python
import os

# Set for current session
os.environ['DESIGNSAFE_USERNAME'] = 'your_username'
os.environ['DESIGNSAFE_PASSWORD'] = 'your_password'

from dapi import DSClient
client = DSClient()
```

### Using .env Files in Jupyter

Create a `.env` file in your notebook directory:

```python
# Create .env file programmatically
with open('.env', 'w') as f:
    f.write('DESIGNSAFE_USERNAME=your_username\n')
    f.write('DESIGNSAFE_PASSWORD=your_password\n')

from dapi import DSClient
client = DSClient()
```

## 🔧 Advanced Configuration

### Custom Base URL

```python
from dapi import DSClient

client = DSClient(
    base_url="https://designsafe.tapis.io",  # Default
    username="your_username",
    password="your_password"
)
```

### Multiple .env Files

```python
from dapi import DSClient

# Development environment
dev_client = DSClient(env_file=".env.development")

# Production environment
prod_client = DSClient(env_file=".env.production")
```

## ✅ Verifying Authentication

### Check Authentication Status

```python
from dapi import DSClient

try:
    client = DSClient()
    print("✅ Authentication successful!")
    
    # Test API access
    apps = client.apps.find("", verbose=False)
    print(f"✅ API access confirmed. Found {len(apps)} apps.")
    
except Exception as e:
    print(f"❌ Authentication failed: {e}")
```

### Test Database Access

```python
# Test database authentication
try:
    df = client.db.ngl.read_sql("SELECT COUNT(*) FROM SITE")
    print("✅ Database access confirmed")
except Exception as e:
    print(f"❌ Database access failed: {e}")
```

## 🚨 Troubleshooting

### Common Authentication Issues

#### Invalid Credentials
```
AuthenticationError: Tapis authentication failed
```
**Solution**: Verify your DesignSafe username and password

#### Network Issues
```
AuthenticationError: An unexpected error occurred during authentication
```
**Solution**: Check internet connection and DesignSafe service status

#### Environment Variable Issues
```
Enter DesignSafe Username: 
```
**Solution**: Verify environment variables are set correctly
```bash
echo $DESIGNSAFE_USERNAME
echo $DESIGNSAFE_PASSWORD
```

#### .env File Not Found
```python
# Verify .env file exists and is readable
import os
print(os.path.exists('.env'))
print(os.access('.env', os.R_OK))
```

### Database Connection Issues

For database-specific authentication issues:

```python
# Check database environment variables
import os
print("NGL_DB_USER:", os.getenv('NGL_DB_USER'))
print("VP_DB_USER:", os.getenv('VP_DB_USER'))
print("EQ_DB_USER:", os.getenv('EQ_DB_USER'))
```

Required database environment variables:
```bash
# NGL Database
export NGL_DB_USER="dspublic"
export NGL_DB_PASSWORD="your_password"
export NGL_DB_HOST="db_host"
export NGL_DB_PORT="3306"

# VP Database  
export VP_DB_USER="dspublic"
export VP_DB_PASSWORD="your_password"
export VP_DB_HOST="db_host"
export VP_DB_PORT="3306"

# Earthquake Recovery Database
export EQ_DB_USER="dspublic"
export EQ_DB_PASSWORD="your_password"
export EQ_DB_HOST="db_host"
export EQ_DB_PORT="3306"
```

## 📖 Example: Complete Setup

Here's a complete example of setting up authentication:

```python
# 1. Create .env file
with open('.env', 'w') as f:
    f.write('DESIGNSAFE_USERNAME=your_username\n')
    f.write('DESIGNSAFE_PASSWORD=your_password\n')
    f.write('NGL_DB_USER=dspublic\n')
    f.write('NGL_DB_PASSWORD=your_db_password\n')
    f.write('NGL_DB_HOST=db_host\n')
    f.write('NGL_DB_PORT=3306\n')

# 2. Initialize client
from dapi import DSClient
client = DSClient()

# 3. Test authentication
print("Testing TAPIS API access...")
apps = client.apps.find("matlab", verbose=False)
print(f"Found {len(apps)} MATLAB apps")

print("Testing database access...")
df = client.db.ngl.read_sql("SELECT COUNT(*) FROM SITE")
print(f"NGL database has {df.iloc[0, 0]} sites")

print("✅ All authentication successful!")
```

## ➡️ Next Steps

After setting up authentication:

1. **[Try the quick start guide](quickstart.md)** for your first workflow
2. **[Submit your first job](jobs.md)** using the jobs interface
3. **[Query databases](database.md)** for research data
4. **[Explore examples](examples/mpm.md)** for detailed workflows