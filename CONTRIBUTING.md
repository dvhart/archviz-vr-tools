Contributions are welcome.

When preparing your changes and your commit messages, please ensure to break up your changes into independent functional changes. Be sure to document each change with short subject line followed by a longer description of the problem and how you intended to fix it. Finally, sign off your commit messages with "Signed-off-by: Your Name \<email address\>" (see http://developercertificate.org).

For example:

```
Fix CroppedAreaTopPixels to work with Google Photos viewer

The joined images worked on my mobile devices, but when opened in Google
Photos on the Google Chrome browser, they would display only black,
despite the thumbnail looking correct and displaying the photosphere and
VR icons.

The CroppedAreaTopPixels property should indicate the number of pixels
to crop. It was set to the image height, but it should have been set to
0.

Change the CroppedAreaTopPixels property to 0. It now renders properly
in Google Photos in the Chrome and Safari browsers, and still renders
properly in stereoscopic VR mode on mobile devices.

Signed-off-by: Darren Hart <dvhart@infradead.org>

```

You can automatically add your Signed-off-by with `git commit -s`.

To submit a contribution, follow the traditional GitHub workflow: https://guides.github.com/activities/forking/
