# Nonsidereal Target Airmass TOM Module

This module adds support for custom ephemerides of moving bodies. The use case
is to observe a newly discovered moving body that is either unknown to the
Minor Planet Center or JPL Horizons Service, or in the case that the ephemerides
provided by each are inaccurate.

This allows the creation of a target that uses user-provided ephemerides, one
for each telescope site, in the JPL format. Observations can be scheduled at
any of the LCO facilities, and the Gemini North and South telescopes.

## Installation:

To be written

## Features in development:

 * interface with the SOAR submission system
 * observation tiler for use in astrometric uncertainty ellipse coverage
