plugin_info = {
    'name': "Example Plugin",
    'Info': "Example plugin demonstrates how plugins work!",
    'Usage': [
        "/example",
        # "/command2",
        # "/etc"
    ]
}
regex = [
    "^[/]example$",
]


def main(msg):
    return "Return Value"
