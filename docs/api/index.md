# API Reference

This section provides comprehensive API documentation for all DAPI modules and classes, automatically generated from docstrings.

## Overview

The DAPI package is organized into several core modules:

### **Core Client**
- **[DSClient](client.md)** - Main client interface for all DAPI functionality

### **Service Modules**
- **[Jobs](jobs.md)** - Job submission, monitoring, and management
- **[Files](files.md)** - File operations and path translation
- **[Apps](apps.md)** - Application discovery and details
- **[Systems](systems.md)** - System information and queue management
- **[Auth](auth.md)** - Authentication and credential management

### **Database Access**
- **[Database](database.md)** - Database connections and query execution

### **Utilities**
- **[Exceptions](exceptions.md)** - Custom exception classes

## Quick Navigation

### **Getting Started**
```python
from dapi import DSClient

# Initialize client
ds = DSClient()

# Access different services
ds.jobs.generate_request(...)
ds.files.upload(...)
ds.db.ngl.read_sql(...)
```

### **Common Operations**
- **Submit Jobs**: `ds.jobs.submit_request(job_dict)`
- **Monitor Jobs**: `submitted_job.monitor()`
- **File Upload**: `ds.files.upload(local_path, remote_uri)`
- **File Download**: `ds.files.download(remote_uri, local_path)`
- **Database Query**: `ds.db.ngl.read_sql("SELECT * FROM table")`

### **Advanced Features**
- **Archive Management**: Custom job result organization
- **Path Translation**: Seamless local/cloud path conversion
- **Parametric Studies**: Batch job submission and monitoring
- **Error Handling**: Comprehensive exception hierarchy

## Documentation Conventions

### **Parameter Types**
- `Optional[Type]` - Parameter can be `None`
- `Union[Type1, Type2]` - Parameter accepts multiple types
- `List[Type]` - List containing elements of specified type
- `Dict[str, Any]` - Dictionary with string keys and any values

### **Return Types**
- Methods clearly document return types and formats
- Async methods return appropriate async types
- Error conditions are documented in `Raises` sections

### **Examples**
Each method includes practical usage examples showing:
- Basic usage patterns
- Parameter combinations
- Error handling
- Integration with other DAPI components

## Cross-References

The API documentation includes extensive cross-references:
- **Method signatures** link to parameter and return types
- **Related methods** are referenced in descriptions
- **Example workflows** demonstrate method integration
- **Error handling** shows exception hierarchies

---

**Browse the API documentation using the navigation menu to explore specific modules and their functionality.**