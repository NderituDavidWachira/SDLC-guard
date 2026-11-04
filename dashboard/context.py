from catalogue.models import Pillar


def pillar_nav(request):
    if not request.user.is_authenticated:
        return {}
    return {'nav_pillars': Pillar.objects.all()}
