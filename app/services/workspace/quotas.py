DEFAULT_QUOTAS = {
    "maxEvents": 1000,
    "maxConnectors": 4,
    "maxUsers": 10
}


workspace_quotas = {}


def get_workspace_quotas():

    return workspace_quotas


def get_workspace_quota(
    workspace_id: str
):

    return workspace_quotas.get(
        workspace_id,
        DEFAULT_QUOTAS
    )


def set_workspace_quota(
    workspace_id: str,
    quota: dict
):

    workspace_quotas[
        workspace_id
    ] = {
        **DEFAULT_QUOTAS,
        **quota
    }

    return workspace_quotas[
        workspace_id
    ]



