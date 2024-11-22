def DS_GetDir(cur_dir, t):
    # cur_dir = os.getcwd()
    if "jupyter/MyData" in cur_dir:
        cur_dir = cur_dir.split("MyData").pop()
        input_dir = t.username + cur_dir
        input_uri = "tapis://{}/{}".format(storage_id, input_dir)
        input_uri = input_uri.replace(" ", "%20")
    elif "jupyter/mydata" in cur_dir:
        cur_dir = cur_dir.split("myData").pop()
        input_dir = t.username + cur_dir
        input_uri = "tapis://{}/{}".format(storage_id, input_dir)
        input_uri = input_uri.replace(" ", "%20")

    elif "jupyter/MyProjects" in cur_dir:
        cur_dir = cur_dir.split("MyProjects/").pop()
        PRJ = cur_dir.split("/")[0]
        cur_dir = cur_dir.split(PRJ).pop()
        import requests

        resp = requests.get(
            f"https://designsafe-ci.org/api/projects/v2/{PRJ}",
            headers={"x-tapis-token": t.access_token.access_token},
        )
        project_uuid = resp.json()["baseProject"]["uuid"]
        input_dir = cur_dir
        input_uri = "tapis://project-{}{}".format(project_uuid, cur_dir)
        input_uri = input_uri.replace(" ", "%20")
    elif "jupyter/projects" in cur_dir:
        cur_dir = cur_dir.split("projects/").pop()
        PRJ = cur_dir.split("/")[0]
        cur_dir = cur_dir.split(PRJ).pop()
        import requests

        resp = requests.get(
            f"https://designsafe-ci.org/api/projects/v2/{PRJ}",
            headers={"x-tapis-token": t.access_token.access_token},
        )
        project_uuid = resp.json()["baseProject"]["uuid"]
        input_dir = cur_dir
        input_uri = "tapis://project-{}{}".format(project_uuid, cur_dir)
        input_uri = input_uri.replace(" ", "%20")
    elif "jupyter/CommunityData" in cur_dir:
        cur_dir = cur_dir.split("jupyter/CommunityData").pop()
        input_dir = cur_dir
        input_uri = "tapis://designsafe.storage.community/{}".format(input_dir)
        input_uri = input_uri.replace(" ", "%20")

    return input_uri


def DS_GetStatus(t, mjobUuid, tlapse=15):
    import time

    print(" Job launched. Status provided below")
    print(
        " Can also check in DesignSafe portal under - Workspace > Tools & Application > Job Status"
    )

    status = t.jobs.getJobStatus(jobUuid=mjobUuid).status
    previous = ""
    while True:
        if status in ["FINISHED", "FAILED", "STOPPED"]:
            break
        status = t.jobs.getJobStatus(jobUuid=mjobUuid).status
        if status == previous:
            continue
        else:
            previous = status
        print(f"\tStatus: {status}")
        time.sleep(tlapse)
    return status


def DS_GetRuntime(t, mjobUuid):
    from datetime import datetime

    print("\nRuntime Summary")
    print("---------------")
    hist = t.jobs.getJobHistory(jobUuid=mjobUuid)

    time1 = datetime.strptime(hist[-1].created, "%Y-%m-%dT%H:%M:%S.%fZ")
    time0 = datetime.strptime(hist[0].created, "%Y-%m-%dT%H:%M:%S.%fZ")
    print("TOTAL   time:", time1 - time0)

    for i in range(len(hist)):
        if hist[i].eventDetail == "RUNNING":
            time1 = datetime.strptime(hist[i + 1].created, "%Y-%m-%dT%H:%M:%S.%fZ")
            time0 = datetime.strptime(hist[i].created, "%Y-%m-%dT%H:%M:%S.%fZ")
            print("RUNNING time:", time1 - time0)
        if hist[i].eventDetail == "QUEUED":
            time1 = datetime.strptime(hist[i + 1].created, "%Y-%m-%dT%H:%M:%S.%fZ")
            time0 = datetime.strptime(hist[i].created, "%Y-%m-%dT%H:%M:%S.%fZ")
            print("QUEUED  time:", time1 - time0)
