"""Keep a variance proxy distinct from a historical realised-drag benchmark."""


def letf_context(lt):
    assumptions = lt.get('assumptions') or {}
    return {
        'prior_quarter_quantity': 'AZ_PROXY_FROM_PRIOR_63_OBSERVATION_VARIANCE',
        'historical_study_fund': '122630',
        'historical_study_scope': 'Past study only; not validation of the current fund, sample or variance proxy',
        'rate_assumption': assumptions.get('funding_rate', 0.0),
        'fee_assumption': lt['fee'],
        'dividends': assumptions.get('dividends', 'OMITTED'),
        'assumptions': assumptions,
        'current_proxy_validation': 'NOT_RUN',
        **{key: lt[key] for key in ('underlying_index', 'index_code', 'index_source',
                                   'index_mapping_source', 'index_status', 'calculation_status')},
    }


def letf_text(lt):
    assumptions = lt.get('assumptions') or {}
    if assumptions.get('mode') == 'EXPLICIT_SCENARIO':
        convention = ('price-return comparison, with beta times the assumed dividend yield added'
                      if assumptions['benchmark'] == 'price_return' else
                      'total-return comparison, with distributions already included and no extra dividend term')
        dividend = (f", dividend yield={assumptions['dividend_yield']:.2%}"
                    if assumptions['dividend_yield'] is not None else '')
        carry = (f"User scenario: {convention}. Annual continuous inputs: funding rate={assumptions['funding_rate']:.2%}, "
                 f"fee={assumptions['annual_fee']:.2%}{dividend}; time=sessions/252. "
                 "Funding, fee and dividend contributions are shown separately. The funding contribution is (1-beta)*r*T "
                 "and can increase an inverse fund's model-relative return. These inputs are assumptions, not observed "
                 "fund costs or verified distributions. ZERO_RATE_REFERENCE remains a separate comparison with the "
                 "legacy fixed fee and omitted dividends. ")
    else:
        carry = (f"Current assumptions: rate=0, annual fee={lt['fee']:.2%}, dividends omitted. "
                 "ZERO_RATE_REFERENCE is a named comparison; the fixed fee is not a verified current fund expense. ")
    return ("AZ variance proxy: the prior 63 observations' variance is inserted into the formula. "
            "This is not observed fund/index realised drag or the study's prior-quarter realised-drag benchmark. "
            "The stored M_E4 study concerns historical 122630; it does not validate this fund, sample or variance proxy. "
            f"Index input: {lt['index_source']}. " + carry +
            "The selected index is a variance input, not the fund's realised futures benchmark. "
            "Funding/dividend terms and real-market validation remain separate limitations. "
            "Do not use these proxies as fund-deviation forecasts or holding recommendations.")


def letf_unavailable_text(lt):
    return (f"LETF calculation NOT_RUN · required index: {lt['underlying_index']}. "
            f"{lt['error']} Other ETF results remain available. "
            "Synthetic index data are used only in explicit Synthetic demo mode.")
