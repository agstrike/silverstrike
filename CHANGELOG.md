# Changelog

All notable changes to SilverStrike will be documented here.

## [Unreleased](https://github.com/agstrike/silverstrike/compare/0.1.1...master)

## [0.1.1](https://github.com/agstrike/silverstrike/releases/tag/0.1.1) - 2018-02-03

### Added
* Baisc REST API based on django-rest-framework #19
* Categories can now be disabled
* Support Django version 2.0
* Support for localization
* Ability to filter hide inactive accounts in the account index
* Add badges to the recurrence index
* Special view for disabled recurrences
* Add view to assign categories to multiple splits at once

### Fixed
* Balance charts now show correct balances
* Upcoming transactions on the dashboard are only displayed once
* Merging accounts correctly updates recurring transactions #44
* Inactive accounts are no longer showed in the charts view #45
* Fix server error in category_spending api call when not enough data is available #32

### Removed
* Support for all Django versions below 2.0
* Ability to sign up using social accounts

## [0.1.0](https://github.com/agstrike/silverstrike/releases/tag/0.1.0) - 2017-12-09

Initial release
