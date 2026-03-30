from googleapiclient.discovery import build

from auth import credentials_from_session


def get_recent_files(credentials_dict: dict, max_results: int = 30) -> list[dict]:
    """Return up to ``max_results`` most recently created non-trashed Drive files."""
    credentials = credentials_from_session(credentials_dict)
    service = build("drive", "v3", credentials=credentials)

    results = (
        service.files()
        .list(
            pageSize=max_results,
            fields=(
                "files(id, name, mimeType, createdTime, modifiedTime, "
                "webViewLink, owners)"
            ),
            orderBy="createdTime desc",
            q="trashed = false",
        )
        .execute()
    )

    files = results.get("files", [])

    formatted: list[dict] = []
    for file in files:
        formatted.append(
            {
                "id": file.get("id", ""),
                "name": file["name"],
                "type": file["mimeType"],
                "created": file.get("createdTime", ""),
                "modified": file["modifiedTime"],
                "link": file.get("webViewLink", ""),
                "owner": file.get("owners", [{}])[0].get("emailAddress", "Unknown"),
            }
        )

    return formatted
