"""Current product-display meanings; never rewrite a stored product report."""


def cms_coupon_context(report):
    """Describe the existing CMS coupon field without repricing or parsing notes.

    The original field is retained as a decimal annualized first-period rate.
    The existing CMS leg detail carries the period-by-period projection.
    Other product coupon/yield conventions are left untouched.
    """
    if not str(getattr(report, 'underlying', '')).startswith('CMS') or report.coupon is None:
        return None
    return {
        'quantity': 'FIRST_PERIOD_EXPECTED_ANNUALIZED_COUPON',
        'value': report.coupon,
        'unit': 'ANNUAL_DECIMAL_RATE',
        'projection': 'FORWARD_CURVE_WITHOUT_CMS_CONVEXITY_ADJUSTMENT',
        'schedule_source': 'CMS_COUPON_LEG_DETAIL',
        'scope': 'FIRST_PERIOD_ONLY',
        'later_coupons': 'SEE_PERIOD_BY_PERIOD_SCHEDULE',
        'payment_guarantee': 'NOT_ESTABLISHED_BY_MODEL',
    }
