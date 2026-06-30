FROM {{ build_step_base }} AS local_base
FROM __EXTERNAL_FROM__ AS external_from
FROM local_base
COPY --from={{ build_step_copy_source }} /markers/build-step-copy-source.txt /markers/build-step-copy-source.txt
COPY --from=external_from /markers/external-from.txt /markers/external-from.txt
COPY --from=__EXTERNAL_COPY__ /markers/external-copy.txt /markers/external-copy.txt
