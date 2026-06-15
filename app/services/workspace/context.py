CURRENT_WORKSPACE = {
    "id": "default"
}


def get_workspace():

    return CURRENT_WORKSPACE


def set_workspace(
    workspace_id
):

    CURRENT_WORKSPACE[
        "id"
    ] = workspace_id

    return CURRENT_WORKSPACE