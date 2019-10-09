# NaNoWriMo API

Before diving into the deep end: This API is not public. It is a backend detail of the NaNoWriMo
site, and as such NaNo is not responsible if this code breaks or if it suddenly changes. I am simply
documenting what is there

## General Description

The NaNo API runs on a very object-driven principle. Most API calls are done through 'type' endpoints,
which return instances of a data type, or perform operations on them. Certain types represent relations
between two other types, and generally are named as a combination of the first and second type. After
a user is logged in, they are given an auth-token. This token must be passed in an `Authorization` header
on all subsequent requests.

## Known Types/Endpoints

### Base URL:

`https://api.nanowrimo.org/`

### General Forms:

* `/{command}`
  * `GET` Retrieves singular data
* `/{type}`
  * `GET` Retrieves list of objects
    * `filter[user_id]={id}` Only returns objects linked to user `id`
    * `include={obj},...` Comma-separated list of object types. Related objects of this type will
    be included in the response
    * `group_types={type},...` Comma-separated list of group types. Only for `group-users` type.
    Incomplete understanding
* `/{type}/{id}`
  * `GET` Retrieves object of `type` with id `id`
  * `PATCH` Edits object
* `/{type}/{command}`
  * `POST` Runs command with given data
* `/{type}/{id}/{type2}`
  * `GET` Retrieves `type2` related to `type`, returns a list

### Known Types:

* users
* projects
* badges
* genres
* groups
* challenges
* nanomessages
* locations
* external-links
* group-external-links
* favorite-books
* favorite-authors

* user-badges
* project-sessions
* project-challenges
* group-users
* location-groups

### Known Commands:

* `fundometer`
  * `GET` Gets donation info
* `search`
  * `GET` Searchs for users by name
    * `q` Name to filter by

* `users/current`
  * `GET` Gets current user
* `users/sign_in`
  * `POST` Logs in user
    * `identifier={user}` Username of the user
    * `password={pass}` Password of the user
* `users/logout`
  * `POST` Logs out user

* `groups/invite_buddy/{id}`
  * `POST` Invites user `id` to be your buddy
* `groups/approve_buddy/{id}`
  * `POST` Approves user `id` as your buddy

## Response Format:

Response is given in JSON. Most responses use the common type request format, though some requests
user their own response formats. Known formats are listed below.

### Type Request

```json
{
  "data": Object,
  "included": [
    Object,
    ...
  ]
}
```

### Object

```json
{
  "id": "{id}",
  "type": "{id}",
  "links": {
    "self": "/{type}/{id}"
  },
  "attributes": {
    "{attr-name}": "{attr-value}",
    ...
  },
  "relationships": {
    "{type-name}": {
      "links": {
        "self": "{type}/{id}/relationships/{type-name}",
        "related": "{type}/{id}/{type-name}"
      },
      "data": [
        {
          "type": "{type-name}",
          "id": "{type-id}"
        },
        ...
      ]
    },
    ...
  }
}
```

### Sign In

```json
{
  "auth_token": "{token}"
}
```

### Error

```json
{
  "error": "{errmsg}"
}
```

### Fundometer

```json
{
  "goal": {goal},
  "raised": "{total-raised}",
  "donorCount": {donor-count}
}
```
