#### Assumptions
1. If there is no clients in the list, there will not be any output
2. Transaction id's are not validated to be unique, but are expected to be unique at least within one client 
3. The data type validation is performed prior to processing (was not addressed)
4. For the decimals regular rounding applies, in case there are for any reason more than 4 decimals past the point
5. Spaces in the file are unexpected. The separator between values must be `,`, not the `,{space}`
6. The column names in the file are fixed to be `type`, `client`, `tx`, `amount` in any order.
7. The output values for decimals always have four places precision, meaning `0` will be output as `0.0000`
8. There is no processing/logging in case of failed/error transactions - they are just skipped
9. There are no any 3rd party dependencies to install before execution
