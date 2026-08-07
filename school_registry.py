from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class SchoolSource:
    canonical_name: str
    roster_url: str
    aliases: tuple[str, ...]
    strong_aliases: tuple[str, ...] = ()
    official_domains: tuple[str, ...] = ()
    country: str = ""
    qs_global_mba_2026_rank: str = ""
    roster_disciplines: tuple[str, ...] = ()

    def roster_url_supports(self, labels: list[str]) -> bool:
        if not self.roster_url:
            return False
        if not self.roster_disciplines:
            return True
        normalized = {_normalize(x) for x in labels}
        supported = {_normalize(x) for x in self.roster_disciplines}
        return bool(normalized & supported)


def _normalize(value: str) -> str:
    value = value.casefold()
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return " ".join(value.split())


def _s(rank, name, country, domains, aliases, strong=(), roster_url="", roster_disciplines=()):
    return SchoolSource(
        canonical_name=name,
        roster_url=roster_url,
        aliases=tuple(aliases),
        strong_aliases=tuple(strong),
        official_domains=tuple(domains),
        country=country,
        qs_global_mba_2026_rank=rank,
        roster_disciplines=tuple(roster_disciplines),
    )


# QS Global MBA Rankings 2026 rank-through-99 cohort. Because the cutoff is tied,
# this contains 101 ranked schools. Two original office schools are retained as
# unranked registry additions for backwards compatibility.
SCHOOL_SOURCES: tuple[SchoolSource, ...] = (
    _s('1', 'University of Pennsylvania (Wharton)', 'United States', ('upenn.edu',), ('wharton', 'upenn wharton', 'university of pennsylvania', 'penn wharton'), ('upenn', 'wharton'), 'https://accounting.wharton.upenn.edu/faculty/faculty-list/', ('accounting', 'accountancy')),
    _s('2', 'Harvard Business School', 'United States', ('hbs.edu', 'harvard.edu'), ('harvard', 'harvard business school', 'hbs'), ('harvard', 'hbs'), '', ()),
    _s('3', 'Massachusetts Institute of Technology (Sloan)', 'United States', ('mit.edu',), ('mit', 'mit sloan', 'massachusetts institute of technology', 'sloan'), ('mit', 'sloan'), 'https://mitsloan.mit.edu/faculty/academic-groups/accounting/faculty-research-centers', ('accounting', 'accountancy')),
    _s('4', 'Stanford University (Graduate School of Business)', 'United States', ('stanford.edu',), ('stanford', 'stanford gsb', 'stanford graduate school of business'), ('stanford', 'stanford gsb'), 'https://www.gsb.stanford.edu/faculty-research/faculty/academic-areas/accounting', ('accounting', 'accountancy')),
    _s('5', 'HEC Paris', 'France', ('hec.edu',), ('hec paris', 'hec'), ('hec paris',), '', ()),
    _s('6', 'London Business School', 'United Kingdom', ('london.edu',), ('london business school', 'lbs'), ('london business school', 'lbs'), '', ()),
    _s('7', 'University of Cambridge (Judge Business School)', 'United Kingdom', ('cam.ac.uk',), ('cambridge judge', 'university of cambridge', 'judge business school', 'cambridge'), ('cambridge', 'judge'), '', ()),
    _s('8', 'INSEAD', 'France', ('insead.edu',), ('insead',), ('insead',), '', ()),
    _s('9', 'Northwestern University (Kellogg)', 'United States', ('northwestern.edu',), ('kellogg', 'northwestern kellogg', 'northwestern university'), ('northwestern', 'kellogg'), 'https://www.kellogg.northwestern.edu/faculty-research/faculty-directory/', ()),
    _s('10', 'Columbia University (Columbia Business School)', 'United States', ('columbia.edu',), ('columbia', 'columbia business school'), ('columbia', 'columbia business'), 'https://business.columbia.edu/faculty/divisions/accounting/faculty', ('accounting', 'accountancy')),
    _s('11', 'IE Business School', 'Spain', ('ie.edu',), ('ie business school', 'ie university business school'), ('ie business',), '', ()),
    _s('=12', 'University of Oxford (Saïd Business School)', 'United Kingdom', ('ox.ac.uk',), ('oxford said', 'said business school', 'university of oxford', 'oxford'), ('oxford', 'said'), '', ()),
    _s('=12', 'Yale School of Management', 'United States', ('yale.edu',), ('yale', 'yale som', 'yale school of management'), ('yale',), '', ()),
    _s('14', 'University of California, Berkeley (Haas)', 'United States', ('berkeley.edu',), ('berkeley haas', 'uc berkeley', 'haas', 'university of california berkeley', 'ucb'), ('berkeley', 'haas', 'ucb'), 'https://haas.berkeley.edu/faculty-research/academic-groups/', ()),
    _s('=15', 'University of Chicago (Booth)', 'United States', ('chicagobooth.edu', 'uchicago.edu'), ('chicago booth', 'university of chicago', 'booth school of business', 'booth'), ('chicago booth', 'booth'), '', ()),
    _s('=15', 'IESE Business School', 'Spain', ('iese.edu',), ('iese', 'iese business school'), ('iese',), '', ()),
    _s('17', 'New York University (Stern)', 'United States', ('nyu.edu',), ('nyu', 'nyu stern', 'new york university', 'stern'), ('nyu', 'stern'), 'https://www.stern.nyu.edu/experience-stern/about/departments-centers-initiatives/academic-departments/accounting/faculty-staff/full-time-faculty', ('accounting', 'accountancy')),
    _s('18', 'University of California, Los Angeles (Anderson)', 'United States', ('ucla.edu',), ('ucla', 'ucla anderson', 'anderson', 'university of california los angeles'), ('ucla', 'anderson'), 'https://www.anderson.ucla.edu/faculty-and-research/accounting/faculty', ('accounting', 'accountancy')),
    _s('19', 'Imperial College Business School', 'United Kingdom', ('imperial.ac.uk',), ('imperial', 'imperial college business school', 'imperial business school'), ('imperial',), '', ()),
    _s('20', 'SDA Bocconi School of Management', 'Italy', ('sdabocconi.it', 'unibocconi.it'), ('sda bocconi', 'bocconi', 'sda bocconi school of management'), ('sda bocconi', 'bocconi'), '', ()),
    _s('21', 'Esade Business School', 'Spain', ('esade.edu',), ('esade', 'esade business school'), ('esade',), '', ()),
    _s('22', 'University of Michigan (Ross)', 'United States', ('umich.edu',), ('michigan ross', 'university of michigan', 'ross', 'michigan'), ('umich', 'ross'), 'https://michiganross.umich.edu/faculty-research/areas-of-study/accounting', ('accounting', 'accountancy')),
    _s('23', 'National University of Singapore (NUS Business School)', 'Singapore', ('nus.edu.sg',), ('nus', 'nus business school', 'national university of singapore'), ('nus',), '', ()),
    _s('24', 'Duke University (Fuqua)', 'United States', ('duke.edu',), ('duke', 'duke fuqua', 'fuqua', 'duke university'), ('duke', 'fuqua'), 'https://www.fuqua.duke.edu/faculty-research/directory/all', ()),
    _s('25', 'IMD Business School', 'Switzerland', ('imd.org',), ('imd', 'imd business school', 'international institute for management development'), ('imd',), '', ()),
    _s('26', 'ESCP Business School', 'France', ('escp.eu',), ('escp', 'escp business school'), ('escp',), '', ()),
    _s('27', 'Copenhagen Business School', 'Denmark', ('cbs.dk',), ('copenhagen business school', 'copenhagen'), ('copenhagen',), '', ()),
    _s('28', 'Tsinghua University (School of Economics and Management)', 'China', ('tsinghua.edu.cn',), ('tsinghua', 'tsinghua sem', 'school of economics and management tsinghua'), ('tsinghua', 'tsinghua sem'), '', ()),
    _s('29', 'ESSEC Business School', 'France', ('essec.edu',), ('essec', 'essec business school'), ('essec',), '', ()),
    _s('30', 'Warwick Business School', 'United Kingdom', ('wbs.ac.uk', 'warwick.ac.uk'), ('warwick', 'warwick business school', 'wbs'), ('warwick', 'wbs'), '', ()),
    _s('31', 'Melbourne Business School', 'Australia', ('mbs.edu', 'unimelb.edu.au'), ('melbourne business school', 'university of melbourne business school'), ('melbourne business',), '', ()),
    _s('32', 'UNSW Business School (AGSM)', 'Australia', ('unsw.edu.au',), ('unsw', 'unsw business school', 'agsm', 'australian graduate school of management'), ('unsw', 'agsm'), '', ()),
    _s('33', 'Cornell University (Johnson)', 'United States', ('cornell.edu',), ('cornell', 'cornell johnson', 'johnson', 'cornell university'), ('cornell', 'johnson'), 'https://business.cornell.edu/faculty-research/accounting/', ('accounting', 'accountancy')),
    _s('34', 'Erasmus University Rotterdam (Rotterdam School of Management)', 'Netherlands', ('rsm.nl', 'eur.nl'), ('erasmus rsm', 'rotterdam school of management', 'rsm', 'erasmus university rotterdam'), ('rsm', 'rotterdam school of management'), '', ()),
    _s('35', 'University of Southern California (Marshall)', 'United States', ('usc.edu',), ('usc marshall', 'southern california marshall', 'university of southern california', 'marshall', 'usc'), ('usc', 'marshall'), 'https://www.marshall.usc.edu/faculty-research/faculty-directory', ()),
    _s('36', 'Boston University (Questrom)', 'United States', ('bu.edu',), ('boston university questrom', 'questrom', 'bu questrom', 'boston university'), ('questrom', 'bu questrom'), '', ()),
    _s('37', 'University of Texas at Austin (McCombs)', 'United States', ('utexas.edu',), ('ut austin', 'texas mccombs', 'university of texas at austin', 'mccombs', 'ut'), ('ut', 'ut austin', 'mccombs'), 'https://www.mccombs.utexas.edu/faculty-and-research/faculty-directory/', ()),
    _s('38', 'Nanyang Technological University (Nanyang Business School)', 'Singapore', ('ntu.edu.sg',), ('nanyang business school', 'ntu singapore', 'nanyang ntu', 'nanyang technological university'), ('nanyang', 'ntu singapore'), '', ()),
    _s('39', 'Alliance Manchester Business School', 'United Kingdom', ('manchester.ac.uk',), ('alliance manchester', 'manchester business school', 'alliance manchester business school'), ('alliance manchester',), '', ()),
    _s('40', 'Frankfurt School of Finance & Management', 'Germany', ('frankfurt-school.de',), ('frankfurt school', 'frankfurt school of finance and management'), ('frankfurt school',), '', ()),
    _s('=41', 'China Europe International Business School (CEIBS)', 'China', ('ceibs.edu',), ('ceibs', 'china europe international business school'), ('ceibs',), '', ()),
    _s('=41', 'Singapore Management University (Lee Kong Chian School of Business)', 'Singapore', ('smu.edu.sg',), ('singapore management university', 'lee kong chian', 'smu singapore'), ('lee kong chian', 'smu singapore'), '', ()),
    _s('43', 'EDHEC Business School', 'France', ('edhec.edu',), ('edhec', 'edhec business school'), ('edhec',), '', ()),
    _s('44', 'University of Sydney Business School', 'Australia', ('sydney.edu.au',), ('university of sydney business school', 'university of sydney', 'usyd business school', 'usyd'), ('usyd',), '', ()),
    _s('45', 'Indiana University (Kelley)', 'United States', ('iu.edu',), ('indiana kelley', 'indiana university', 'iu kelley', 'kelley'), ('iu', 'kelley', 'indiana'), 'https://kelley.iu.edu/faculty-research/faculty-directory/', ()),
    _s('=46', 'Carnegie Mellon University (Tepper)', 'United States', ('cmu.edu',), ('carnegie mellon tepper', 'tepper', 'cmu tepper', 'carnegie mellon university'), ('tepper', 'cmu'), '', ()),
    _s('=46', 'Mannheim Business School', 'Germany', ('mannheim-business-school.com', 'uni-mannheim.de'), ('mannheim business school', 'university of mannheim business school', 'mannheim'), ('mannheim',), '', ()),
    _s('48', 'University of St. Gallen', 'Switzerland', ('unisg.ch',), ('st gallen', 'university of st gallen', 'hsg'), ('st gallen', 'hsg'), '', ()),
    _s('=49', 'emlyon business school', 'France', ('em-lyon.com',), ('emlyon', 'em lyon', 'emlyon business school'), ('emlyon', 'em lyon'), '', ()),
    _s('=49', 'Hong Kong University of Science and Technology (HKUST Business School)', 'Hong Kong', ('hkust.edu.hk',), ('hkust', 'hkust business school', 'hong kong university of science and technology'), ('hkust',), '', ()),
    _s('51', 'University of Hong Kong (HKU Business School)', 'Hong Kong', ('hku.hk',), ('hku', 'hku business school', 'university of hong kong'), ('hku',), '', ()),
    _s('52', 'Indian Institute of Management Bangalore', 'India', ('iimb.ac.in',), ('iim bangalore', 'iimb', 'indian institute of management bangalore'), ('iimb', 'iim bangalore'), '', ()),
    _s('53', 'Georgia Institute of Technology (Scheller)', 'United States', ('gatech.edu',), ('georgia tech scheller', 'georgia institute of technology', 'scheller', 'gatech'), ('georgia tech', 'scheller', 'gatech'), '', ()),
    _s('54', 'Johns Hopkins University (Carey Business School)', 'United States', ('jhu.edu',), ('johns hopkins carey', 'carey business school', 'johns hopkins university'), ('johns hopkins', 'carey'), '', ()),
    _s('55', 'University of Toronto (Rotman)', 'Canada', ('utoronto.ca',), ('toronto rotman', 'university of toronto', 'rotman'), ('rotman', 'university of toronto'), '', ()),
    _s('56', 'EGADE Business School', 'Mexico', ('tec.mx',), ('egade', 'egade business school', 'tecnologico de monterrey egade', 'tec de monterrey egade'), ('egade',), '', ()),
    _s('57', 'WHU – Otto Beisheim School of Management', 'Germany', ('whu.edu',), ('whu', 'otto beisheim', 'whu otto beisheim'), ('whu', 'otto beisheim'), '', ()),
    _s('58', 'Indian Institute of Management Ahmedabad', 'India', ('iima.ac.in',), ('iim ahmedabad', 'iima', 'indian institute of management ahmedabad'), ('iima', 'iim ahmedabad'), '', ()),
    _s('59', 'Peking University (Guanghua School of Management)', 'China', ('pku.edu.cn',), ('peking university', 'pku', 'guanghua', 'guanghua school of management'), ('pku', 'guanghua'), '', ()),
    _s('60', 'University of Amsterdam (Amsterdam Business School)', 'Netherlands', ('uva.nl',), ('amsterdam business school', 'university of amsterdam', 'uva business school'), ('amsterdam business school',), '', ()),
    _s('61', 'Georgetown University (McDonough)', 'United States', ('georgetown.edu',), ('georgetown mcDonough', 'georgetown mcdonough', 'mcdonough', 'georgetown university'), ('georgetown', 'mcdonough'), '', ()),
    _s('62', 'Dartmouth College (Tuck)', 'United States', ('dartmouth.edu',), ('dartmouth tuck', 'tuck', 'tuck school of business', 'dartmouth college'), ('dartmouth', 'tuck'), '', ()),
    _s('63', 'University of Florida (Warrington)', 'United States', ('ufl.edu',), ('florida warrington', 'university of florida', 'uf warrington', 'warrington', 'uf'), ('uf', 'warrington', 'florida'), 'https://warrington.ufl.edu/directory/', ()),
    _s('64', 'Indian Institute of Management Calcutta', 'India', ('iimcal.ac.in',), ('iim calcutta', 'iimc', 'indian institute of management calcutta'), ('iimc', 'iim calcutta'), '', ()),
    _s('65', 'POLIMI Graduate School of Management', 'Italy', ('polimi.it',), ('polimi graduate school of management', 'polimi', 'politecnico di milano graduate school of management'), ('polimi',), '', ()),
    _s('=66', 'Grenoble Ecole de Management', 'France', ('grenoble-em.com',), ('grenoble ecole de management', 'grenoble school of management', 'gem'), ('grenoble', 'gem'), '', ()),
    _s('=66', 'University of Edinburgh Business School', 'United Kingdom', ('ed.ac.uk',), ('edinburgh business school', 'university of edinburgh business school', 'university of edinburgh'), ('edinburgh business', 'university of edinburgh'), '', ()),
    _s('68', 'Shanghai Jiao Tong University (Antai College of Economics and Management)', 'China', ('sjtu.edu.cn',), ('shanghai jiao tong', 'sjtu', 'antai', 'antai college'), ('sjtu', 'antai'), '', ()),
    _s('69', 'Cranfield School of Management', 'United Kingdom', ('cranfield.ac.uk',), ('cranfield', 'cranfield school of management', 'cranfield university'), ('cranfield',), '', ()),
    _s('70', 'University of Virginia (Darden)', 'United States', ('virginia.edu',), ('virginia darden', 'university of virginia', 'uva darden', 'darden'), ('darden', 'uva darden'), '', ()),
    _s('71', 'Texas A&M University (Mays)', 'United States', ('tamu.edu',), ('texas a&m mays', 'texas a and m mays', 'tamu', 'mays', 'texas a&m university'), ('tamu', 'mays', 'texas a&m'), '', ()),
    _s('72', 'Emory University (Goizueta)', 'United States', ('emory.edu',), ('emory goizueta', 'emory university', 'goizueta'), ('emory', 'goizueta'), '', ()),
    _s('=73', 'Babson College (F.W. Olin Graduate School of Business)', 'United States', ('babson.edu',), ('babson', 'babson olin', 'f w olin graduate school babson', 'babson college'), ('babson', 'babson olin'), '', ()),
    _s('=73', 'McGill University (Desautels)', 'Canada', ('mcgill.ca',), ('mcgill desautels', 'mcgill university', 'desautels'), ('mcgill', 'desautels'), '', ()),
    _s('75', 'Leeds University Business School', 'United Kingdom', ('leeds.ac.uk',), ('leeds university business school', 'university of leeds business school', 'leeds'), ('leeds business', 'university of leeds'), '', ()),
    _s('76', 'Pennsylvania State University (Smeal)', 'United States', ('psu.edu',), ('penn state', 'penn state smeal', 'smeal', 'pennsylvania state university'), ('penn state', 'psu', 'smeal'), 'https://www.smeal.psu.edu/accounting/people/faculty', ('accounting', 'accountancy')),
    _s('=77', 'Audencia Business School', 'France', ('audencia.com',), ('audencia', 'audencia business school'), ('audencia',), '', ()),
    _s('=77', 'University of Minnesota (Carlson)', 'United States', ('umn.edu',), ('minnesota carlson', 'university of minnesota', 'carlson school of management', 'carlson'), ('minnesota carlson', 'carlson'), '', ()),
    _s('79', 'Washington University in St. Louis (Olin)', 'United States', ('wustl.edu',), ('washu olin', 'washington university st louis', 'washington university in st louis', 'wustl olin'), ('washu', 'wustl', 'washu olin'), 'https://olin.wustl.edu/faculty-and-research/academic-areas/accounting/', ('accounting', 'accountancy')),
    _s('80', 'Michigan State University (Broad)', 'United States', ('msu.edu',), ('michigan state broad', 'michigan state university', 'broad college of business', 'msu'), ('michigan state', 'msu', 'broad'), '', ()),
    _s('81', 'University of Washington (Foster)', 'United States', ('uw.edu',), ('uw foster', 'washington foster', 'university of washington', 'foster'), ('uw', 'foster'), 'https://foster.uw.edu/faculty-research/academic-departments/accounting/faculty/', ('accounting', 'accountancy')),
    _s('=82', 'Fudan University (School of Management)', 'China', ('fudan.edu.cn',), ('fudan', 'fudan school of management', 'fudan university'), ('fudan',), '', ()),
    _s('=82', 'Vlerick Business School', 'Belgium', ('vlerick.com',), ('vlerick', 'vlerick business school'), ('vlerick',), '', ()),
    _s('84', 'ESMT Berlin', 'Germany', ('esmt.berlin',), ('esmt', 'esmt berlin', 'european school of management and technology'), ('esmt',), '', ()),
    _s('85', 'Chinese University of Hong Kong (CUHK Business School)', 'Hong Kong', ('cuhk.edu.hk',), ('cuhk', 'cuhk business school', 'chinese university of hong kong'), ('cuhk',), '', ()),
    _s('=86', 'University of Cape Town Graduate School of Business', 'South Africa', ('uct.ac.za',), ('uct gsb', 'cape town gsb', 'university of cape town business school', 'university of cape town graduate school of business'), ('uct', 'uct gsb', 'cape town gsb'), '', ()),
    _s('=86', 'University of Notre Dame (Mendoza)', 'United States', ('nd.edu',), ('notre dame', 'notre dame mendoza', 'mendoza', 'university of notre dame'), ('notre dame', 'mendoza'), 'https://mendoza.nd.edu/mendoza-directory/', ()),
    _s('88', 'INCAE Business School', 'Costa Rica', ('incae.edu',), ('incae', 'incae business school', 'instituto centroamericano de administracion de empresas'), ('incae',), '', ()),
    _s('89', 'Rice University (Jones)', 'United States', ('rice.edu',), ('rice', 'rice jones', 'jones graduate school', 'rice university'), ('rice', 'rice jones'), 'https://business.rice.edu/faculty-research/academic-areas/accounting', ('accounting', 'accountancy')),
    _s('90', 'Durham University Business School', 'United Kingdom', ('durham.ac.uk',), ('durham business school', 'durham university business school', 'durham university'), ('durham business', 'durham university'), '', ()),
    _s('91', 'University of Texas at Dallas (Jindal)', 'United States', ('utdallas.edu',), ('ut dallas', 'utd', 'utd jindal', 'jindal school of management', 'university of texas at dallas'), ('ut dallas', 'utd', 'jindal'), '', ()),
    _s('92', 'University of North Carolina at Chapel Hill (Kenan-Flagler)', 'United States', ('unc.edu',), ('unc', 'unc chapel hill', 'unc kenan flagler', 'kenan flagler', 'university of north carolina'), ('unc', 'kenan flagler'), 'https://www.kenan-flagler.unc.edu/faculty/', ()),
    _s('93', 'Western University (Ivey)', 'Canada', ('uwo.ca',), ('western ivey', 'ivey business school', 'western university ivey', 'uwo ivey'), ('ivey', 'uwo'), '', ()),
    _s('94', 'Trinity College Dublin Business School', 'Ireland', ('tcd.ie',), ('trinity business school', 'trinity college dublin', 'tcd business school', 'tcd'), ('tcd', 'trinity college dublin'), '', ()),
    _s('95', 'Luiss Business School', 'Italy', ('luiss.it',), ('luiss business school', 'luiss'), ('luiss',), '', ()),
    _s('96', 'Bayes Business School', 'United Kingdom', ('citystgeorges.ac.uk', 'city.ac.uk'), ('bayes business school', 'bayes', 'city bayes'), ('bayes',), '', ()),
    _s('97', 'George Washington University School of Business', 'United States', ('gwu.edu',), ('george washington university business school', 'george washington school of business', 'gwu business', 'gwu'), ('gwu', 'george washington'), '', ()),
    _s('=98', 'City University of Hong Kong (College of Business)', 'Hong Kong', ('cityu.edu.hk',), ('cityu hong kong', 'city university of hong kong business', 'cityu college of business', 'cityu'), ('cityu',), '', ()),
    _s('=98', 'Qatar University (College of Business and Economics)', 'Qatar', ('qu.edu.qa',), ('qatar university business', 'qatar university college of business', 'qu qatar'), ('qatar university', 'qu qatar'), '', ()),
    _s('=99', 'University of Queensland Business School', 'Australia', ('uq.edu.au',), ('uq business school', 'university of queensland business school', 'university of queensland', 'uq'), ('uq',), '', ()),
    _s('=99', 'York University (Schulich)', 'Canada', ('yorku.ca',), ('york schulich', 'schulich school of business', 'york university schulich'), ('schulich', 'york schulich'), '', ()),
    _s('', 'University of Illinois Urbana-Champaign (Gies)', 'United States', ('illinois.edu',), ('illinois gies', 'uiuc', 'university of illinois', 'gies'), ('uiuc', 'gies'), 'https://giesbusiness.illinois.edu/faculty-research/faculty-profiles?department=BA', ()),
    _s('', 'University of Georgia (Terry)', 'United States', ('uga.edu',), ('georgia terry', 'university of georgia', 'uga terry', 'terry'), ('uga', 'terry'), 'https://www.terry.uga.edu/faculty-research/departments/accounting/', ('accounting', 'accountancy')),
 )


RANKED_SCHOOL_COUNT = sum(bool(s.qs_global_mba_2026_rank) for s in SCHOOL_SOURCES)
REGISTRY_SCHOOL_COUNT = len(SCHOOL_SOURCES)


_ALIAS_INDEX: dict[str, SchoolSource] = {}
for source in SCHOOL_SOURCES:
    for name in (source.canonical_name, *source.aliases):
        key = _normalize(name)
        existing = _ALIAS_INDEX.get(key)
        if existing is not None and existing != source:
            raise RuntimeError(f"Duplicate school alias: {name}")
        _ALIAS_INDEX[key] = source


_MATCH_STOPWORDS = {"school", "business", "graduate", "college", "the", "of"}


def _match_normalize(value: str) -> str:
    normalized = _normalize(value)
    tokens = [t for t in normalized.split() if t not in _MATCH_STOPWORDS]
    return " ".join(tokens)


_MATCH_INDEX: dict[str, SchoolSource] = {}
_MATCH_FORMS: list[tuple[SchoolSource, str]] = []
for source in SCHOOL_SOURCES:
    for name in (source.canonical_name, *source.aliases):
        form = _match_normalize(name)
        if not form:
            continue
        existing = _MATCH_INDEX.get(form)
        if existing is None:
            _MATCH_INDEX[form] = source
        elif existing != source:
            _MATCH_INDEX.pop(form, None)
        _MATCH_FORMS.append((source, form))


def resolve_known_school(school_name: str) -> SchoolSource | None:
    """Resolve flexible school names in the built-in global registry.

    Strong aliases use longest-match-wins. This lets `UT` resolve to McCombs,
    while `UT Dallas` resolves to Jindal, and lets `Michigan State` beat the
    shorter `Michigan` form when both are present. If the longest match remains
    ambiguous, the resolver returns None rather than guessing.
    """
    normalized_input = _normalize(school_name)
    input_tokens = set(normalized_input.split())

    strong_hits: list[tuple[SchoolSource, int]] = []
    for source in SCHOOL_SOURCES:
        for alias in source.strong_aliases:
            alias_tokens = _normalize(alias).split()
            if alias_tokens and set(alias_tokens).issubset(input_tokens):
                strong_hits.append((source, len(alias_tokens)))

    if strong_hits:
        best_len = max(length for _, length in strong_hits)
        best_sources=[]
        for source,length in strong_hits:
            if length == best_len and source not in best_sources:
                best_sources.append(source)
        if len(best_sources)==1:
            return best_sources[0]
        return None

    exact = _ALIAS_INDEX.get(normalized_input)
    if exact is not None:
        return exact

    relaxed = _match_normalize(school_name)
    if not relaxed:
        return None
    relaxed_exact = _MATCH_INDEX.get(relaxed)
    if relaxed_exact is not None:
        return relaxed_exact

    input_set=set(relaxed.split())
    scored: dict[SchoolSource,int] = {}
    for source,form in _MATCH_FORMS:
        form_set=set(form.split())
        if not form_set:
            continue
        if form_set.issubset(input_set):
            score=80+min(len(form_set),10)
        elif input_set.issubset(form_set):
            score=75+min(len(input_set),10)
        else:
            overlap=len(input_set & form_set)
            union=len(input_set | form_set)
            score=round(70*overlap/union) if union else 0
        scored[source]=max(scored.get(source,0),score)
    if not scored:
        return None
    ranked=sorted(scored.items(), key=lambda item:item[1], reverse=True)
    best_source,best_score=ranked[0]
    second_score=ranked[1][1] if len(ranked)>1 else -1
    if best_score>=82 and best_score-second_score>=4:
        return best_source
    return None
