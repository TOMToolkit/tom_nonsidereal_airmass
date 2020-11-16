from datetime import datetime, timedelta
from bisect import bisect_left
from astropy.coordinates import Angle, AltAz
from astropy import units
from astropy.time import Time
import ephem
import numpy as np
import json

from tom_observations import facility

EPHEM_FORMAT = '%Y/%m/%d %H:%M:%S'

DEFAULT_VALUES = {
    'epoch': '2000'
}

d2r = np.pi/180.0

def ephem_to_datetime(ephem_time):
    """
    Converts PyEphem time object to a datetime object
    :param ephem_time: time to be converted to datetime
    :type ephem_time: PyEphem date
    :returns: datetime time equivalent to the ephem_time
    :rtype: datetime
    """
    return datetime.strptime(str(ephem_time), EPHEM_FORMAT)


def get_rise_set(observer, target, start_time, end_time):
    """
    Calculates all of the rises and sets for a target, from a position on Earth,
    within a given window.
    If the target is up at the start time, the rise is included in the result
    despite not being within the window. Similarly, if the target is up at the
    end time, the next setting beyond the end window is included in the result.
    :param observer: Represents the position from which to calculate the rise/sets
    :type observer: PyEphem Observer
    :param target: The object for which to calculate the rise/sets
    :type target: Target
    :param start_time: start of the calculation window
    :type start_time: datetime
    :param end_time: end of the calculation window
    :type end_time: datetime
    :returns: A list of 2-tuples, each a pair of values representing a rise and a set, both datetime objects
    :rtype: list
    """
    if end_time < start_time:
        raise Exception('Start must be before end')
    observer.date = start_time
    start_time = start_time
    rise_set = []
    previous_setting = ephem_to_datetime(observer.previous_setting(target))
    previous_rising = ephem_to_datetime(observer.previous_rising(target))
    if previous_rising > previous_setting:
        next_setting = ephem_to_datetime(observer.next_setting(target))
        rise_set.append((previous_rising, next_setting))
        start_time = next_setting + timedelta(seconds=1)
    while start_time < end_time:
        observer.date = start_time
        next_rising = ephem_to_datetime(observer.next_rising(target))
        next_setting = ephem_to_datetime(observer.next_setting(target))
        if next_rising > start_time and next_rising < end_time:
            rise_set.append((next_rising, next_setting))
        start_time = next_setting + timedelta(seconds=1)
    return rise_set


def get_last_rise_set_pair(rise_sets, time):
    """
    Gets the rise/set pair for the last rise before the given time, using a
    binary search
    :param rise_sets: array of tuples representing set of rise/sets to search
    :type rise_sets: array
    :param time: time value used to find the most recent rise, in UNIX time
    :type time: float
    :returns: Most recent rise/set pair with respect to the given time
    :rtype: tuple
    """
    last_rise_pos = bisect_left(rise_sets, (time,))
    if last_rise_pos <= 0:
        return None
    return rise_sets[last_rise_pos-1]


def get_next_rise_set_pair(rise_sets, time):
    """
    Gets the upcoming rise/set pair for the next rise after the given time,
    using a binary search
    :param rise_sets: array of tuples representing set of rise/sets to search
    :type rise_sets: array
    :param time: time value used to find the next rise, in UNIX time
    :type time: float
    :returns: Soonest upcoming rise/set with respect to the given time
    :rtype: tuple
    """
    next_rise_pos = bisect_left(rise_sets, (time,))
    if next_rise_pos >= len(rise_sets):
        return None
    return rise_sets[next_rise_pos]

### WF: need to duplicate this function but as get_eph_scheme_visibilty
###     do as was done with get_eph_scheme_arc.
###     Then modify nonsidereal_target_plan in templatetags/nonsidereal_airmass_extras
###     to use the PLOTTING_FUNCTION style checks and imports
def get_eph_scheme_visibility(target, start_time, end_time, interval, airmass_limit=10):
    """
    Calculates the airmass for an epehermis scheme target for each given
    interval between the start and end times.
    The resulting data omits any airmass above the provided limit (or
    default, if one is not provided), as well as any airmass calculated
    during the day.
    :param start_time: start of the window for which to calculate the airmass
    :type start_time: datetime
    :param end_time: end of the window for which to calculate the airmass
    :type end_time: datetime
    :param interval: time interval, in minutes, at which to calculate airmass within the given window
    :type interval: int
    :param airmass_limit: maximum acceptable airmass for the resulting calculations
    :type airmass_limit: int
    :returns: A dictionary containing the airmass data for each site. The dict keys consist of the site name prepended
        with the observing facility. The values are the airmass data, structured as an array containing two arrays. The
        first array contains the set of datetimes used in the airmass calculations. The second array contains the
        corresponding set of airmasses calculated.
    :rtype: dict
    """
    if not airmass_limit:
        airmass_limit = 10

    eph_json = json.loads(target.eph_json)
    sites_with_eph = list(eph_json.keys())

    visibility = {}
    sun = ephem.Sun()
    for observing_facility in facility.get_service_classes():
        observing_facility_class = facility.get_service_class(observing_facility)
        sites = observing_facility_class().get_observing_sites()
        for site, site_details in sites.items():
            site_code = site_details['sitecode']
            if site_code in sites_with_eph:
                print('Using',site_code)
                mjds, ras, decs = [], [], []
                for i in range(len(eph_json[site_code])):
                    mjds.append(eph_json[site_code][i]['t'])
                    ras.append(eph_json[site_code][i]['R'])
                    decs.append(eph_json[site_code][i]['D'])

                mjds, ras, decs = np.array(mjds, dtype='float64'), np.array(ras, dtype='float64'), np.array(decs, dtype='float64')
                min_mjd, max_mjd = np.min(mjds), np.max(mjds)

                min_time = Time(max(min_mjd, Time(str(start_time)).mjd), format='mjd')
                max_time = Time(min(max_mjd, Time(str(end_time)).mjd), format='mjd')
                print(min_time, max_time)
                interval_days = float(interval)/(60.0*24.0)
                interp_times = np.arange(min_time.mjd, max_time.mjd, interval_days)
                interp_ra = np.interp(interp_times, mjds, ras)*d2r
                interp_dec = np.interp(interp_times, mjds, decs)*d2r
                if min_time<max_time:
                    start, end =  datetimeFromTime(min_time), datetimeFromTime(max_time)
                    positions = [[], []]
                    observer = observer_for_site(site_details)
                    rise_sets = get_rise_set(observer, sun, start, end)
                    body = ephem.FixedBody()
                    curr_interval = start
                    n = 0
                    while curr_interval <= end:
                        time = curr_interval
                        #print(time)
                        last_rise_set = get_last_rise_set_pair(rise_sets, time)
                        sunup = time > last_rise_set[0] and time < last_rise_set[1] if last_rise_set else False
                        observer.date = curr_interval
                        body._ra = interp_ra[n]
                        body._dec = interp_dec[n]
                        body.compute(observer)
                        alt = Angle(str(body.alt), unit=units.degree)
                        az = Angle(str(body.az), unit=units.degree)
                        altaz = AltAz(alt=alt.to_string(unit=units.rad), az=az.to_string(unit=units.rad))
                        airmass = altaz.secz
                        positions[0].append(curr_interval)
                        positions[1].append(
                            airmass.value if (airmass.value > 1 and airmass.value <= airmass_limit) and not sunup else None
                        )
                        curr_interval += timedelta(minutes=interval)
                    visibility['({0}) {1}'.format(observing_facility, site)] = positions
            else:
                print('Missing', site_code)
    return visibility


def get_visibility(target, start_time, end_time, interval, airmass_limit=10):
    """
    Calculates the airmass for a target for each given interval between
    the start and end times.
    The resulting data omits any airmass above the provided limit (or
    default, if one is not provided), as well as any airmass calculated
    during the day.
    :param start_time: start of the window for which to calculate the airmass
    :type start_time: datetime
    :param end_time: end of the window for which to calculate the airmass
    :type end_time: datetime
    :param interval: time interval, in minutes, at which to calculate airmass within the given window
    :type interval: int
    :param airmass_limit: maximum acceptable airmass for the resulting calculations
    :type airmass_limit: int
    :returns: A dictionary containing the airmass data for each site. The dict keys consist of the site name prepended
        with the observing facility. The values are the airmass data, structured as an array containing two arrays. The
        first array contains the set of datetimes used in the airmass calculations. The second array contains the
        corresponding set of airmasses calculated.
    :rtype: dict
    """
    if not airmass_limit:
        airmass_limit = 10
    visibility = {}
    body = get_pyephem_instance_for_type(target)
    sun = ephem.Sun()
    for observing_facility in facility.get_service_classes():
        observing_facility_class = facility.get_service_class(observing_facility)
        sites = observing_facility_class().get_observing_sites()
        for site, site_details in sites.items():
            positions = [[], []]
            observer = observer_for_site(site_details)
            rise_sets = get_rise_set(observer, sun, start_time, end_time)
            curr_interval = start_time
            while curr_interval <= end_time:
                time = curr_interval
                last_rise_set = get_last_rise_set_pair(rise_sets, time)
                sunup = time > last_rise_set[0] and time < last_rise_set[1] if last_rise_set else False
                observer.date = curr_interval
                body.compute(observer)
                alt = Angle(str(body.alt), unit=units.degree)
                az = Angle(str(body.az), unit=units.degree)
                altaz = AltAz(alt=alt.to_string(unit=units.rad), az=az.to_string(unit=units.rad))
                airmass = altaz.secz
                positions[0].append(curr_interval)
                positions[1].append(
                    airmass.value if (airmass.value > 1 and airmass.value <= airmass_limit) and not sunup else None
                )
                curr_interval += timedelta(minutes=interval)
            visibility['({0}) {1}'.format(observing_facility, site)] = positions
    return visibility


def get_arc(target):
    """
    Get the approximate arc for plotting purposes. Not accurate enough for telescope pointing.
    """

    body = get_pyephem_instance_for_type(target)
    sun = ephem.Sun()
    observer = ephem.Observer()
    observer.lon = ephem.degrees(0.0)
    observer.lat = ephem.degrees(0.0)
    observer.elevation = -6371.0

    current_mjd = Time.now().mjd
    ra, dec = [], []
    for i in range(0, 375, 10):
        observer.date = current_mjd + i -15019.5
        body.compute(observer)
        ra.append(Angle(str(body.a_ra), unit=units.degree).value)
        dec.append(Angle(str(body.a_dec), unit=units.degree).value)
    return (ra, dec)


def get_pyephem_instance_for_type(target):
    """
    Constructs a pyephem body corresponding to the proper object type
    in order to perform positional calculations for the target
    :returns: FixedBody or EllipticalBody
    :raises Exception: When a target type other than sidereal or non-sidereal is supplied
    """
    if target.type == target.NON_SIDEREAL:
        body = ephem.EllipticalBody()
        body._inc = ephem.degrees(target.inclination) if target.inclination else 0
        body._Om = target.lng_asc_node if target.lng_asc_node else 0
        body._om = target.arg_of_perihelion if target.arg_of_perihelion else 0
        body._a = target.semimajor_axis if target.semimajor_axis else 0
        body._M = target.mean_anomaly if target.mean_anomaly else 0
        if target.ephemeris_epoch:
            epoch_M = Time(target.ephemeris_epoch, format='jd')
            epoch_M.format = 'datetime'
            body._epoch_M = ephem.Date(epoch_M.value)
        else:
            body._epoch_M = ephem.Date(DEFAULT_VALUES['epoch'])
        body._epoch = target.epoch if target.epoch else ephem.Date(DEFAULT_VALUES['epoch'])
        body._e = target.eccentricity if target.eccentricity else 0
        return body
    else:
        raise Exception("Object type is unsupported for visibility calculations")


def observer_for_site(site):
    observer = ephem.Observer()
    observer.lon = ephem.degrees(str(site.get('longitude')))
    observer.lat = ephem.degrees(str(site.get('latitude')))
    observer.elevation = site.get('elevation')
    return observer


def get_eph_scheme_arc(target):
    eph_json = json.loads(target.eph_json)
    site = list(eph_json.keys())[0]
    eph_json_single = eph_json[site]
    mjd, ra, dec = [], [] , []
    for i in range(0, len(eph_json_single)):
        mjd.append(eph_json_single[i]['t'])
        ra.append(eph_json_single[i]['R'])
        dec.append(eph_json_single[i]['D'])
    mjd, ra, dec = np.array(mjd, dtype='float64'), np.array(ra, dtype='float64'), np.array(dec, dtype='float64')
    step = max(1, int(10.0/(mjd[1]-mjd[0])))
    l = len(ra[::step])
    return (ra[::step] if l>1 else ra, dec[::step] if l>1 else dec)


def datetimeFromTime(t):
    s = t.iso
    (date, time) = s.split()
    Date = date.split('-')
    year = int(float(Date[0]))
    month = int(float(Date[1]))
    day = int(float(Date[2]))
    stime = time.split(':')
    hour = int(float(stime[0]))
    minute = int(float(stime[1]))
    second = int(float(stime[2]))
    return datetime(year, month, day, hour, minute, second)
