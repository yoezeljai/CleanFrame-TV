# Public release review

Prepared 20 October 2026. CleanFrame began on one personal Samsung The Frame. Very little portability work has been done. The README presents it as a starting point to fork and adapt at the user's own risk.

## Source boundary

The public source contains the current 0.6.1 app, public-font screenshot, development tools, browser tests, setup notes and asset notices. Research folders, design studies, draft writing, unused Grid/optics code and obsolete generated images were removed after the owner's approval. Recoverable copies remain outside the public source.

Paid Pangram fonts, signing keys, account tokens, local device addresses, recovery state and personal signed widgets remain in ignored local storage. Public preview and export use only Manrope, Geist and Newsreader. The public font check also verifies the expected font files and hashes.

## Asset review

Each of the fifteen wallpaper pages was checked for author and Unsplash licence on 20 October 2026; see [asset sources](asset-sources.md). ABC and SBS icons now use documented MIT Custom Brand Icons sources. Font and icon licence texts are retained. Original code uses MIT; third-party assets keep their own terms in [third-party notices](../THIRD_PARTY_NOTICES.md).

## Validation

The release candidate is validated from a separate clean source snapshot without private setup. Checks cover installation of development dependencies, runtime source/resources, public-source paths and font hashes, Chromium interaction behaviour, and an unsigned public-font export. Asset generators are checked separately. These checks do not establish physical-TV behaviour.

A Gitleaks scan of the two pre-release Git commits found no credential leaks. The cleaned source snapshot is scanned separately before publication. Automated checks are bounded: they cannot guarantee the absence of every possible secret or establish third-party rights beyond the documented source review.

The GitHub check workflow is prepared for public fonts and browser validation. Its first hosted run still needs verification after the source is pushed.

## Publication boundary

The existing private Git history contains the removed studies. Deleting current files does not remove those earlier versions. The proposed first public version starts with a new root commit containing only the reviewed source. The original history is backed up privately. Replacing GitHub main requires the owner's explicit approval for that one-time history replacement.

At the GitHub inventory check, the repository was private, with one main branch, no tags, no releases, no Actions runs and no Actions artifacts. Recheck that inventory before changing visibility. Publication and history replacement remain pending approval. Verify the remote source and unauthenticated public view after any approved visibility change.

Keep public downloads to the unsigned public-font export with its notices. Personal signed packages can contain proprietary fonts. Reference-device installation results are recorded in [TV status](tv-status.md); the public-source review did not contact or change the TV.
