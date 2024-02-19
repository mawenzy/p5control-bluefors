HDFView 3.1.4
------------------------------------------------------------------------------

This directory contains the binary (release) distribution of
HDFView 3.1.4 that was compiled on:
      Windows win-amd64

with:  Java JDK 16.0.1

It was built with the following options:
   -- SHARED HDF 4.2.15
   -- SHARED HDF5 1.10.9

===========================================================================
Note: By default HDFView runs on the included Java JRE 16.
===========================================================================

The contents of this directory are:

   COPYING                 - Copyright notice
   README.txt              - This file
   HDFView-3.1.4.exe (or .msi)  - HDFView Installer

Running
===========================================================================
To install HDFView for Windows:

1. Execute HDFView-3.1.4.exe (or .msi)
2. Follow prompts
3. Execute install-dir\HDFView.exe
===========================================================================

The executable will be in the installation location,
    which by default is at C:\Users\user-name\AppData\Local\HDF_Group\HDFView

The general directory layout for each of the supported platforms follows:
===========================================================================
Linux
===========================================================================
HDFView/
  bin/            // Application launchers
    HDFView
  lib/
    app/
      doc/        // HDFView documents
      extra/      // logging jar for simple logs
      mods/       // Application duplicates
      samples/    // HDFView sample files
      HDFView.cfg     // Configuration info, created by jpackage
      HDFView.jar     // JAR file, copied from the --input directory
    runtime/      // Java runtime image
===========================================================================
macOS
===========================================================================
HDFView.app/
  Contents/
    Info.plist
    MacOS/         // Application launchers
      HDFView
    Resources/           // Icons, etc.
    app/
      doc/        // HDFView documents
      extra/      // logging jar for simple logs
      mods/       // Application duplicates
      samples/    // HDFView sample files
      HDFView.cfg     // Configuration info, created by jpackage
      HDFView.jar     // JAR file, copied from the --input directory
    runtime/      // Java runtime image
===========================================================================
Windows
===========================================================================
HelloWorld/
  HDFView.exe       // Application launchers
  app/
    doc/        // HDFView documents
    extra/      // logging jar for simple logs
    mods/       // Application duplicates
    samples/    // HDFView sample files
    HDFView.cfg     // Configuration info, created by jpackage
    HDFView.jar     // JAR file, copied from the --input directory
  runtime/      // Java runtime image
===========================================================================

Documentation for this release can be found at the following URL:
   https://portal.hdfgroup.org/display/HDFVIEW/HDFView

See the HDF-JAVA home page for further details:
   https://www.hdfgroup.org/downloads/hdfview/

Bugs should be reported to help@hdfgroup.org.