# checks that plain GET /system lists every /system route the app publishes, so a new route is not left off

from GitHub_Connector import api


def test_index_lists_every_published_system_route():
    # reads the published routes from the OpenAPI document; the list's query hint is for a person reading it
    listed = {route.split("?")[0] for route in api.index()["routes"]}
    published = {
        f"{method.upper()} {path}"
        for path, operations in api.app.openapi()["paths"].items()
        if path.startswith("/system/")
        for method in operations
    }

    assert listed == published
