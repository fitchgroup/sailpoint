=========
Changelog
=========

Version 1.7
===========
- Adding get_attribute_map and provisioning policies
- Adding retry for governance group member retrival
- Fix formatting and adding get_id_by_alias function
- Added function to update Governance group
- Fixing docstrings
- Adding new gg_membership report and get_descriptions function
- Changing retry and timeouts, and setting logs to warning level
- Added function for getting account attribute value
- Formatting and get_all_entitlements should return a generator
- Adding cancel_old_approvals function
- Changes to support new API call for unoptimized aggregation
- Added function - get_entitlement Modified existing function for listing account
- Adding recipient_id as a filter to get_approvals
- Fixing parameters
- Adding get_approvals function
- Updating description of APIs that are used
- Fixing API calls
- Adding get_account function

Version 1.6
===========
- Fixing reference to API
- Report was including users with the wrong lifeCycle state
- Adding warning message for deprecated API use
- Adding docstrings
- Fixing return
- adding update idn obj function and cleaning up pretty logging
- get_api_obj function added
- Fixing typos
- Fixing typo
- Adding governance group functions now v3/beta compliant
- Adding timeout to API calls
- Removing unnecessarily verbose logging
- Removing unnecessarily verbose logging
- Adding query parameter to main_search
- Adjusting logging levels

Version 1.5
===========
- Include nested objects when getting IDs
- Search changed to use searchAfter paging
- Added remove_account function
- Add additional functions, main_search and update doc tags
- Add requstable parameter to create_ap
- Reduce logging to debug, and add exception handling
- Add retry and reduce logging to debug only
- Add list source attributes
- Add ability to toggle comments on requests and denials to the AP
- Search now support >10k records using search_after verses offset
- Updating changelog
- Updating readme with links to GitHub Page documentation.
- Updating GitHub hosted links

Version 1.4
===========

- Public release published to GitHub https://github.com/fitchgroup/sailpoint

Version 1.3
===========

- Internal Release ready for publication

Version 0.1
===========

- Initial Release
