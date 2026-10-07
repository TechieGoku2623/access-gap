#!/usr/bin/env bash
set +e
access-gap county --fips 48105 --therapy zolgensma --summary; access-gap county --fips 48201 --therapy casgevy --summary
exit $?
