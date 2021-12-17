from typing import Optional


def db_version_supports_custom_certificates(db_version: Optional[str]) -> bool:
    # 1. If db_version is None => Latest DB version is used (which already supported custom certificates in EXAConf
    # 2. If db_version is "default" => Return True, as "default" is lexically greater than "7.0.5"
    # 3. Return result of db version comparison
    if db_version in (None, "default"):
        return True
    else:
        db_version_ = db_version
        if db_version_.endswith("-d1"):
            db_version_ = "-".join(db_version.split("-")[0:-1])
        version = tuple([int(v) for v in db_version_.split(".")])
        if len(version) != 3:
            raise ValueError(f"Invalid db version given: {db_version}")
        return version > (7, 0, 5)
