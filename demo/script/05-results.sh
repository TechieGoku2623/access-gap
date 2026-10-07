#!/usr/bin/env bash
set +e
access-gap report --summary --dest /tmp/access-gap-report.html --therapy zolgensma
exit $?
