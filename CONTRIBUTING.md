# Contributing to SilverStrike

Thanks for concidering to contribute! Even if not explicitly said, it's appreciated!

You can contribute in different ways. You can write code, file bugs and feature requests.
If you're more of a designer (I'm not) you are very welcome to help with layouts. In case you know more than just english you can help translating.

### Reporting Bugs

If you found a flaw, search for it in the open and closed issues. If you can't find anything proceed with opening an issue.

> **Note:** If you find a **Closed** issue that seems like it is the same thing that you're experiencing, open a new issue and include a link to the original issue in the body of your new one.

Explain the problem and include additional details to help reproduce the problem:

* **Use a clear and descriptive title** for the issue to identify the problem.
* **Describe the exact steps which reproduce the problem** in as many details as possible. 
* **Describe the behavior you observed after following the steps** and point out what exactly is the problem with that behavior.
* **Explain which behavior you expected to see instead and why.**
* **Include screenshots** if you think they are helpful
* **If you're reporting that an unhandled exception**, include a stack trace. If it's rather small, include it in the issue itself. Otherwise please attach it as a file or paste the content to some pasting service like [dpaste](https://dpaste.de)
* **Can you reproduce the problem in the [demo](https://demo.silverstrike.tk)?**

### Translation

Translation is done using [crowdin](https://crowdin.com/project/silverstrike). You should be able to translate and suggest translations for existing languages right after creating an account there. If you would like to rights to approve suggestions for specific languages or add entirely new languages, don't hesitate to contact me on crowdin.


### Feature Requests

I'm always looking for good features to add to SilverStrike. Before creating a new issue for it try searching the existing issues labled `feature-request`. If you found it, use the thumbs up and add comments if you want to detail something specific. Otherwise open a new issue.

* **Use a clear and descriptive title** for the issue to identify the suggestion.
* **Provide a step-by-step description of the suggested enhancement** in as many details as possible.
* **Explain why this enhancement would be useful**.

### Your First Code Contribution

Unsure where to begin contributing? I'll try to add issues with `beginner` and `help-wanted` labels.
They will most likely be easiest to fix if you're unfamiliar with Django or the code itself.

### Pull Requests

* Do not include issue numbers in the PR title
* Make sure the tests pass locally by running `tox`
* If travis shows errors, please fix them
* Please try to write tests to cover the code you introduce

### Git Commit Messages

* Use the present tense ("Add feature" not "Added feature")
* Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
* Limit the first line to 72 characters or less
* Reference issues and pull requests after the first line
* If you think travis builds aren't needed include `[ci skip]` in the commit description


This page is heavily inspired by the [contribution guide](https://github.com/atom/atom/blob/master/CONTRIBUTING.md) of [atom](https://atom.io/)
