from corehq.apps.reports.fields import ReportField
from corehq.apps.reports.fields import SelectFilteredMobileWorkerField
from corehq.apps.fixtures.models import FixtureDataType, FixtureDataItem
from corehq.apps.reports.filters.base import BaseSingleOptionFilter
from corehq.apps.reports.filters.users import LinkedUserFilter


class SiteField(ReportField):
    slug = "hsph_site"
    domain = 'hsph'
    slugs = dict(site="hsph_site",
            district="hsph_district",
            region="hsph_region")
    template = "hsph/fields/sites.html"

    def update_context(self):
        self.context['sites'] = self.getFacilities(domain=self.domain)
        self.context['selected'] = dict(region=self.request.GET.get(self.slugs['region'], ''),
                                        district=self.request.GET.get(self.slugs['district'], ''),
                                        siteNum=self.request.GET.get(self.slugs['site'], ''))
        self.context['slugs'] = self.slugs

    @classmethod
    def getFacilities(cls, domain=None):
        cls.domain = domain or cls.domain
        facs = dict()
        data_type = FixtureDataType.by_domain_tag(cls.domain, 'site').first()
        fixtures = FixtureDataItem.by_data_type(cls.domain, data_type.get_id)
        for fix in fixtures:
            region = fix.fields.get("region_id")
            district = fix.fields.get("district_id")
            site = fix.fields.get("site_number")
            if region not in facs:
                facs[region] = dict(name=fix.fields.get("region_name"), districts=dict())
            if district not in facs[region]["districts"]:
                facs[region]["districts"][district] = dict(name=fix.fields.get("district_name"), sites=dict())
            if site not in facs[region]["districts"][district]["sites"]:
                facs[region]["districts"][district]["sites"][site] = dict(name=fix.fields.get("site_name"))
        return facs


class NameOfFADAField(SelectFilteredMobileWorkerField):
    slug = "fada_name"
    name = "Name of FADA"
    group_names = ["Role - FADA"]
    cssId = "fada_name"
    show_only_group_option = False
    default_option = "All FADAs"


class NameOfFIDAField(SelectFilteredMobileWorkerField):
    slug = "fida_name"
    name = "Name of FIDA"
    group_names = ["Role - FIDA"]
    cssId = "fida_name"
    show_only_group_option = False
    default_option = "All FIDAs"

class NameOfCATIField(SelectFilteredMobileWorkerField):
    slug = "cati_name"
    name = "Name of CATI"
    cssId = "cati_name"
    group_names = ["Role - CATI"]
    show_only_group_option = False
    default_option = "All CATIs"

class NameOfCATITLField(SelectFilteredMobileWorkerField):
    slug = "cati_tl_name"
    name = "Name of CATI TL"
    cssId = "cati_tl_name"
    group_names = ["Role - CATI TL"]
    show_only_group_option = False
    default_option = "All CATI TLs"
    

class NameOfCITLField(SelectFilteredMobileWorkerField):
    slug = "citl_name"
    name = "Name of CITL"
    cssId = "citl_name"
    group_names = ["CITL"]


class NameOfDCTLField(BaseSingleOptionFilter):
    domain = 'hsph'
    slug = "dctl_name"
    label = "Name of DCTL"
    default_text = "All DCTLs..."

    @property
    def options(self):
        return self.get_dctl_list()

    @classmethod
    def get_dctl_list(cls):
        data_type = FixtureDataType.by_domain_tag(cls.domain, 'dctl').first()
        data_items = FixtureDataItem.by_data_type(cls.domain, data_type.get_id if data_type else None)
        return [(item.fields.get("name"), item.fields.get("id")) for item in data_items]

    @classmethod
    def get_users_per_dctl(cls):
        dctls = dict()
        data_type = FixtureDataType.by_domain_tag(cls.domain, 'dctl').first()
        data_items = FixtureDataItem.by_data_type(cls.domain, data_type.get_id if data_type else None)
        for item in data_items:
            dctls[item.fields.get("id")] = item.get_users(wrap=False)
        return dctls


class DCTLToFIDAFilter(LinkedUserFilter):
    domain = 'hsph'
    user_types = ("DCTL", "FIDA")


class AllocatedToFilter(BaseSingleOptionFilter):
    slug = "allocated_to"
    label = "Allocated To"
    options = [
        ('cati', 'CATI'),
        ('field', 'Field')
    ]
    default_text = "All"


class SelectReferredInStatusField(BaseSingleOptionFilter):
    slug = "referred_in_status"
    label = "Referred In Status"
    default_text = "All Birth Data"
    options = [
        ('referred', "Only Referred In Births"),
    ]


class SelectCaseStatusField(BaseSingleOptionFilter):
    slug = "case_status"
    label = "Home Visit Status"
    default_text = "Select Status..."
    options = [
        ('closed', "CLOSED"),
        ('open', "OPEN"),
    ]


class IHForCHFField(BaseSingleOptionFilter):
    slug = "ihf_or_chf"
    label = "IHF/CHF"
    domain = 'hsph'
    default_text = "IHF and CHF"
    options = [
        ('IHF', "IHF only"),
        ('CHF', "CHF only"),
    ]

    @classmethod
    def _get_facilities(cls, domain=None):
        domain = domain or cls.domain
        facilities = dict(ihf=[], chf=[])
        data_type = FixtureDataType.by_domain_tag(domain, 'site').first()
        data_items = FixtureDataItem.by_data_type(domain, data_type.get_id)
        for item in data_items:
            ihf_chf = item.fields.get("ihf_chf", "").lower()
            if ihf_chf == 'ifh':  # typo in some test data
                ihf_chf = 'ihf'

            try:
                facilities[ihf_chf].append(item.fields)
            except KeyError:
                # there's a site fixture item without an IHF/CHF value
                pass

        return facilities

    @classmethod
    def get_facilities(cls, domain=None):
        domain = domain or cls.domain
        return dict([(ihf_chf, map(lambda f: f['site_id'], facilities))
                     for (ihf_chf, facilities)
                     in cls._get_facilities(domain).items()])

    @classmethod
    def get_selected_facilities(cls, site_map, domain=None):
        domain = domain or cls.domain
        def filter_by_sitefield(facilities):
            ret = []

            for f in facilities:
                region_id = f['region_id']
                if region_id not in site_map:
                    continue

                district_id = f['district_id']
                districts = site_map[region_id]['districts']
                if district_id not in districts:
                    continue

                site_number = f['site_number']
                if site_number in districts[district_id]['sites']:
                    ret.append(f['site_id'])
            return ret

        return dict([(ihf_chf.lower(), filter_by_sitefield(facilities))
                     for (ihf_chf, facilities)
                     in cls._get_facilities(domain).items()])


class FacilityStatusField(BaseSingleOptionFilter):
    slug = "facility_status"
    label = "Facility Status"
    default_text = "Select Status..."
    options = [
        ('-1', "On Board"),
        ('0', "S.B.R. Deployed"),
        ('1', "Baseline"),
        ('2', "Trial Data"),
    ]


class FacilityField(BaseSingleOptionFilter):
    slug = "facility"
    domain = 'hsph'
    label = "Facility"
    default_text = "All Facilities..."

    @property
    def options(self):
        return [(f['val'], f['text']) for f in self.getFacilities()]

    @classmethod
    def getFacilities(cls, domain=None):
        domain = domain or cls.domain
        data_type = FixtureDataType.by_domain_tag(domain, 'site').first()
        data_items = FixtureDataItem.by_data_type(domain, data_type.get_id)
        return [dict(text=item.fields.get("site_name"), val=item.fields.get("site_id")) for item in data_items]
