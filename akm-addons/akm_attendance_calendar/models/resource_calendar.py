# Copyright 2019 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
import math
import pytz
from pytz import timezone, utc
from datetime import datetime, time, timedelta
from dateutil import relativedelta
from odoo.osv import expression
from odoo.tools.float_utils import float_round
from collections import defaultdict
from dateutil.rrule import rrule, DAILY, WEEKLY
from functools import partial
from itertools import chain

def _boundaries(intervals, opening, closing):
    """ Iterate on the boundaries of intervals. """
    for start, stop, recs in intervals:
        if start < stop:
            yield (start, opening, recs)
            yield (stop, closing, recs)

class Intervals(object):
    """ Collection of ordered disjoint intervals with some associated records.
        Each interval is a triple ``(start, stop, records)``, where ``records``
        is a recordset.
    """
    def __init__(self, intervals=()):
        self._items = []
        if intervals:
            # normalize the representation of intervals
            append = self._items.append
            starts = []
            recses = []
            for value, flag, recs in sorted(_boundaries(intervals, 'start', 'stop')):
                if flag == 'start':
                    starts.append(value)
                    recses.append(recs)
                else:
                    start = starts.pop()
                    if not starts:
                        append((start, value, recses[0].union(*recses)))
                        recses.clear()

    def __bool__(self):
        return bool(self._items)

    def __len__(self):
        return len(self._items)

    def __iter__(self):
        return iter(self._items)

    def __reversed__(self):
        return reversed(self._items)

    def __or__(self, other):
        """ Return the union of two sets of intervals. """
        return Intervals(chain(self._items, other._items))

    def __and__(self, other):
        """ Return the intersection of two sets of intervals. """
        return self._merge(other, False)

    def __sub__(self, other):
        """ Return the difference of two sets of intervals. """
        return self._merge(other, True)

    def _merge(self, other, difference):
        """ Return the difference or intersection of two sets of intervals. """
        result = Intervals()
        append = result._items.append

        # using 'self' and 'other' below forces normalization
        bounds1 = _boundaries(self, 'start', 'stop')
        bounds2 = _boundaries(other, 'switch', 'switch')

        start = None                    # set by start/stop
        recs1 = None                    # set by start
        enabled = difference            # changed by switch
        for value, flag, recs in sorted(chain(bounds1, bounds2)):
            if flag == 'start':
                start = value
                recs1 = recs
            elif flag == 'stop':
                if enabled and start < value:
                    append((start, value, recs1))
                start = None
            else:
                if not enabled and start is not None:
                    start = value
                if enabled and start is not None and start < value:
                    append((start, value, recs1))
                enabled = not enabled

        return result

def float_to_time(hours):
    """ Convert a number of hours into a time object. """
    if hours == 24.0:
        return time.max
    fractional, integral = math.modf(hours)
    return time(int(integral), int(float_round(60 * fractional, precision_digits=0)), 0)

def hour_rounder(t):
    # Rounds to nearest hour by adding a timedelta hour if minute >= 30
    return (t.replace(second=0, microsecond=0, minute=0, hour=t.hour))
            # + timedelta(hours=t.minute//60))

class ResourceCalendar(models.Model):
    _inherit = "resource.calendar"

    def _attendance_intervals_batch(self, start_dt, end_dt, resources=None, domain=None, tz=None):
        """ Return the attendance intervals in the given datetime range.
            The returned intervals are expressed in specified tz or in the resource's timezone.
        """
        self.ensure_one()
        resources = self.env['resource.resource'] if not resources else resources
        assert start_dt.tzinfo and end_dt.tzinfo
        self.ensure_one()
        combine = datetime.combine

        resources_list = list(resources) + [self.env['resource.resource']]
        resource_ids = [r.id for r in resources_list]
        domain = domain if domain is not None else []
        domain = expression.AND([domain, [
            ('calendar_id', '=', self.id),
            ('resource_id', 'in', resource_ids),
            ('display_type', '=', False),
        ]])

        # for each attendance spec, generate the intervals in the date range
        cache_dates = defaultdict(dict)
        cache_deltas = defaultdict(dict)
        result = defaultdict(list)
        for attendance in self.env['resource.calendar.attendance'].search(domain):
            for resource in resources_list:
                # express all dates and times in specified tz or in the resource's timezone
                tz = tz if tz else timezone((resource or self).tz)
                if (tz, start_dt) in cache_dates:
                    start = cache_dates[(tz, start_dt)]
                else:
                    start = start_dt.astimezone(tz)
                    cache_dates[(tz, start_dt)] = start
                if (tz, end_dt) in cache_dates:
                    end = cache_dates[(tz, end_dt)]
                else:
                    end = end_dt.astimezone(tz)
                    cache_dates[(tz, end_dt)] = end

                start = start.date()
                if attendance.date_from:
                    start = max(start, attendance.date_from)
                until = end.date()
                if attendance.date_to:
                    until = min(until, attendance.date_to)
                if attendance.week_type:
                    start_week_type = int(math.floor((start.toordinal()-1)/7) % 2)
                    if start_week_type != int(attendance.week_type):
                        # start must be the week of the attendance
                        # if it's not the case, we must remove one week
                        start = start + relativedelta(weeks=-1)
                weekday = int(attendance.dayofweek)

                days = rrule(DAILY, start, until=until, byweekday=weekday)
                if self.two_weeks_calendar and attendance.week_type:
                    days = rrule(WEEKLY, start, interval=2, until=until, byweekday=weekday)
                # else:
                #     days = rrule(DAILY, start, until=until, byweekday=weekday)

                for day in days:
                    # attendance hours are interpreted in the resource's timezone
                    hour_from = attendance.hour_from
                    if (tz, day, hour_from) in cache_deltas:
                        dt0 = cache_deltas[(tz, day, hour_from)]
                    else:
                        dt0 = tz.localize(combine(day, float_to_time(hour_from)))
                        cache_deltas[(tz, day, hour_from)] = dt0

                    hour_to = attendance.hour_to
                    if attendance.day_period=='night':
                        day_to = day + timedelta(days=1)
                    else:
                        day_to = day

                    if (tz, day_to, hour_to) in cache_deltas:
                        dt1 = cache_deltas[(tz, day_to, hour_to)]
                    else:
                        dt1 = tz.localize(combine(day_to, float_to_time(hour_to)))
                        cache_deltas[(tz, day_to, hour_to)] = dt1
                    result[resource.id].append((max(cache_dates[(tz, start_dt)], dt0), min(cache_dates[(tz, end_dt)], dt1), attendance))
        return {r.id: Intervals(result[r.id]) for r in resources_list}

    def get_work_hours_count(self, start_dt, end_dt, compute_leaves=True, domain=None):
        # Set timezone in UTC if no timezone is explicitly given
        if not start_dt.tzinfo:
            start_dt = start_dt.replace(tzinfo=utc)
        if not end_dt.tzinfo:
            end_dt = end_dt.replace(tzinfo=utc)

        if compute_leaves:
            intervals = self._work_intervals_batch(start_dt, end_dt, domain=domain)[False]
        else:
            intervals = self._attendance_intervals_batch(start_dt, end_dt)[False]

        return sum(self._get_work_hours_interval(start, stop, meta) for start, stop, meta in intervals)

    def _compute_hours_per_day(self, attendances):
        if not attendances:
            return 0

        hour_count = 0.0
        for attendance in attendances:
            hour_count += self._get_work_hours_attendance(attendance)

        if self.two_weeks_calendar:
            number_of_days = len(set(attendances.filtered(lambda cal: cal.week_type == '1').mapped('dayofweek')))
            number_of_days += len(set(attendances.filtered(lambda cal: cal.week_type == '0').mapped('dayofweek')))
        else:
            number_of_days = len(set(attendances.mapped('dayofweek')))

        return float_round(hour_count / float(number_of_days), precision_digits=2)

    def list_leaves(self, from_datetime, to_datetime, calendar=None, domain=None):
        resource = self.resource_id
        calendar = calendar or self.resource_calendar_id

        # naive datetimes are made explicit in UTC
        if not from_datetime.tzinfo:
            from_datetime = from_datetime.replace(tzinfo=utc)
        if not to_datetime.tzinfo:
            to_datetime = to_datetime.replace(tzinfo=utc)

        attendances = calendar._attendance_intervals_batch(
            from_datetime, to_datetime, resource
        )[resource.id]
        leaves = calendar._leave_intervals_batch(
            from_datetime, to_datetime, resource, domain
        )[resource.id]
        result = []
        for start, stop, leave in leaves & attendances:
            hours = self._get_work_hours_interval(start, stop, leave)
            result.append((start.date(), hours, leave))
        return result

    def _get_work_hours_interval(self, start, stop, meta):
        rest = timedelta(hours=sum([attendance.rest_time for attendance in meta])) if (stop-start).total_seconds() / 3600 > 5 else timedelta(hours=0)
        return (stop-start-rest).total_seconds() / 3600

    def _get_rest_hours_interval(self, start, stop, meta):
        start = hour_rounder(start) + timedelta(hours=1)
        stop = hour_rounder(stop)
        rest = timedelta(hours=sum([attendance.rest_time for attendance in meta])) if (stop-start).total_seconds() / 3600 > 5 else timedelta(hours=0)
        return (rest).total_seconds() / 3600

    def _get_work_hours_attendance(self, attendance):
        if attendance.day_period=='night':
            res = attendance.hour_to + 24 - attendance.hour_from - attendance.rest_time
        else:
            res = attendance.hour_to - attendance.hour_from - attendance.rest_time
        return res

    @api.depends('attendance_ids.hour_from', 'attendance_ids.hour_to')
    def _compute_hours_per_week(self):
        for calendar in self:
            sum_hours = sum((attendance.hour_to + 24 - attendance.hour_from) if attendance.day_period=='night' else (attendance.hour_to - attendance.hour_from) for attendance in calendar.attendance_ids)
            calendar.hours_per_week = sum_hours / 2 if calendar.two_weeks_calendar else sum_hours

    def _check_overlap(self, attendance_ids):
        """ attendance_ids correspond to attendance of a week,
            will check for each day of week that there are no superimpose. """
        result = []
        for attendance in attendance_ids.filtered(lambda att: not att.date_from and not att.date_to):
            # 0.000001 is added to each start hour to avoid to detect two contiguous intervals as superimposing.
            # Indeed Intervals function will join 2 intervals with the start and stop hour corresponding.
            if attendance.day_period == 'night':
                result.append((int(attendance.dayofweek) * 24 + attendance.hour_from + 0.000001,
                               int(attendance.dayofweek) * 24 + (attendance.hour_to+24), attendance))
            else:
                result.append((int(attendance.dayofweek) * 24 + attendance.hour_from + 0.000001,
                               int(attendance.dayofweek) * 24 + attendance.hour_to, attendance))

        if len(Intervals(result)) != len(result):
            raise ValidationError(_("Attendances can't overlap."))

    def get_work_duration_simple(self, start_dt, end_dt, domain=None, tz=None):
        self.ensure_one()
        combine = datetime.combine
        domain = domain if domain is not None else []
        domain = expression.AND([domain, [
            ('calendar_id', '=', self.id),
            ('display_type', '=', False),
        ]])

        cache_dates = defaultdict(dict)
        cache_deltas = defaultdict(dict)
        interval = []
        wh = 0
        rt = 0
        for attendance in self.env['resource.calendar.attendance'].search(domain):
            # express all dates and times in specified tz or in the resource's timezone
            tz = tz if tz else timezone('UTC')
            tz = pytz.timezone(self._context.get('tz', 'utc') or 'utc')
            if (tz, start_dt) in cache_dates:
                start = cache_dates[(tz, start_dt)]
            else:
                start = start_dt.astimezone(tz)
                cache_dates[(tz, start_dt)] = start
            if (tz, end_dt) in cache_dates:
                end = cache_dates[(tz, end_dt)]
            else:
                end = end_dt.astimezone(tz)
                cache_dates[(tz, end_dt)] = end

            start = start.date()
            if attendance.date_from:
                start = max(start, attendance.date_from)
            until = end.date()
            if attendance.date_to:
                until = min(until, attendance.date_to)
            if attendance.week_type:
                start_week_type = int(math.floor((start.toordinal()-1)/7) % 2)
                if start_week_type != int(attendance.week_type):
                    # start must be the week of the attendance
                    # if it's not the case, we must remove one week
                    start = start + relativedelta(weeks=-1)
            weekday = int(attendance.dayofweek)

            days = rrule(DAILY, start, until=until, byweekday=weekday)
            if self.two_weeks_calendar and attendance.week_type:
                days = rrule(WEEKLY, start, interval=2, until=until, byweekday=weekday)

            for day in days:
                # attendance hours are interpreted in the resource's timezone
                hour_from = attendance.hour_from
                if (tz, day, hour_from) in cache_deltas:
                    dt0 = cache_deltas[(tz, day, hour_from)]
                else:
                    dt0 = tz.localize(combine(day, float_to_time(hour_from)))
                    cache_deltas[(tz, day, hour_from)] = dt0

                if attendance.day_period=='night':
                    day_to = day + timedelta(days=1)
                else:
                    day_to = day
                hour_to = attendance.hour_to
                if (tz, day_to, hour_to) in cache_deltas:
                    dt1 = cache_deltas[(tz, day_to, hour_to)]
                else:
                    dt1 = tz.localize(combine(day_to, float_to_time(hour_to)))
                    cache_deltas[(tz, day_to, hour_to)] = dt1

                res_start = max(cache_dates[(tz, start_dt)], dt0)
                res_end = min(cache_dates[(tz, end_dt)], dt1)
                if res_start != dt0:
                    res_start = hour_rounder(res_start) + timedelta(hours=1)
                if res_end != dt1:
                    res_end = hour_rounder(res_end)
                hours = self._get_work_hours_interval(res_start,res_end,attendance)
                rests = self._get_rest_hours_interval(res_start,res_end,attendance)
                if hours>0:
                    wh += hours
                if rests>0:
                    rt += rests
                if hours>0 or rests>0:
                    interval.append((res_start, res_end, attendance))

        return {'hours': wh, 'rests': rt, 'interval': interval}

class ResourceCalendarAttendance(models.Model):

    _inherit = "resource.calendar.attendance"

    rest_start = fields.Float(string="Rest Time", compute='_get_rest_start', readonly=False)
    rest_time = fields.Float(string="Rest Duration")
    day_period = fields.Selection(selection_add=[('night', 'Night')], required=True, ondelete={'night': 'set default'})

    @api.depends('hour_from', 'hour_to')
    def _get_rest_start(self):
        for x in self:
            if x.day_period=='night':
                if x.hour_from > x.hour_to and x.hour_to>0 and x.hour_from>0:
                    rest_gross = ((24+x.hour_to)-x.hour_from)/2
                    rest_nett = rest_gross+x.hour_from
                    x.rest_start = (rest_nett - (1/2)) % 24
            else:
                if x.hour_from < x.hour_to and x.hour_to>0 and x.hour_from>0:
                    rest_gross = (x.hour_to-x.hour_from)/2
                    rest_nett = rest_gross+x.hour_from
                    x.rest_start = (rest_nett - (1/2)) % 24

    @api.onchange('hour_from', 'hour_to')
    def _onchange_hours(self):
        # avoid negative or after midnight
        self.hour_from = min(self.hour_from, 23.99)
        self.hour_from = max(self.hour_from, 0.0)
        self.hour_to = min(self.hour_to, 23.99)
        self.hour_to = max(self.hour_to, 0.0)

        # avoid wrong order
        if self.day_period=='night':
            self.hour_to = min(self.hour_to, self.hour_from)
        else:
            self.hour_to = max(self.hour_to, self.hour_from)

    @api.onchange("rest_time")
    def _onchange_rest_time(self):
        # avoid negative or after midnight
        self.rest_time = min(self.rest_time, 23.99)
        self.rest_time = max(self.rest_time, 0.0)

    @api.constrains("hour_from", "hour_to", "rest_time")
    def _check_rest_time(self):
        for record in self:
            if record.day_period=="night":
                if record.hour_to +24 - record.hour_from < record.rest_time:
                    raise ValidationError(
                        _("Rest time cannot be greater than the interval time")
                    )
            else:
                if record.hour_to - record.hour_from < record.rest_time:
                    raise ValidationError(
                        _("Rest time cannot be greater than the interval time")
                    )

class ResourceMixin(models.AbstractModel):
    _inherit = "resource.mixin"

    def _get_work_hours(self, start, stop, meta):
        return (
            stop
            - start
            - timedelta(hours=sum([attendance.rest_time for attendance in meta]))
        ).total_seconds() / 3600
