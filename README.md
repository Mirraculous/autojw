# SteamPriceFetcher (aka autojw)

This script automatically fetches prices in a specific country's Steam Store for a provided list of application names and then automatically sorts them by price descending. 

Made it for myself just for fun when I was offered to pick a free Steam game from the list of 700 🤡

Script is using an undocumented Steam Web API call *api/storesearch/*

## Config

All configuration variables are at the top of the script: 

* ```country``` - Country code *(e.g. ```RU```, ```UA```, ```US```)*
* ```appnames_filename``` - File with the application names which prices need to be fetched (one app name per line) (aka *input file*)
* ```request_delay``` - The delay in seconds between each request to Steam API.
* ```checkpoint_interval``` - A checkpoint file will be written each time *N* apps from the input file are processed. Set to 0 to disable. Checkpoint is written in JSON. Loading from checkpoint is not implemented yet. And very possible that it will never be 🫠
* ```output_dir``` - Output directory where the result files will be created.
* #### Output files
    * ```result_filename``` - The apps that were successfully found will be placed there, along with their price, App ID. Apps are sorted by price descending.
    * ```multiple_filename``` - When the search request returns more than one result for a query, only the first result is written to the *result* file. The additional results will be placed in this file in JSON format.
    * ```not_found_filename``` - If the API request returns no results for the query, the app name will be placed here. The script then tries to truncate the search by removing one word from the end of the app name at a time. If the app is found during this procedure, the truncated name will be written in this file beside the original name, as well as added to *result*, and, possibly, to *multiple* files (with their original name from the input file for reference).
    * ```error_filename``` - If there is an error during an API request, the app name will be placed here, along with the request URL and exception message.
    * ```checkpoint_filename``` - The checkpoint file.