
def extract_modulename_for_build_steps(path: str):
    return path.replace("/", "_").replace(".", "_")
