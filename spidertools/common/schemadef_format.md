# Schemadef Formatting

The schemadef is how the GenericDatabase understands a database schema. It is generic across SQL
flavors, in theory

## Top Level

```
{
  "sql_flavor": "mysql|postgresql",
  "tables": Table Object
}
```

# Table Object

```
{
  "table_name": {
    "columns": [Column Object, ...],
    "primary": ["primary_key", "primary_key_2"],
    "foreign": [Foreign Key Object, ...]
  },
  ...
}
```

# Column Object

```
{
  "name": "col_name",
  "type": "col_type",
  "not_null": true|false,  // If missing, assumed false
  "is_unique": true|false,  // If missing, assumed false
  "default": "default value"
}
```

# Foreign Key Object

```
{
  "local_name": "col_name",
  "remote_name": "col_name",  // If missing, assumed same as local
  "remote_table": "table_name",  // Must exist in the schemadef
  "on_delete": "action"  // One of CASCADE, RESTRICT, SET NULL, SET DEFAULT. Optional
  "on_update": "action"  // Same as above. Optional
}
```
