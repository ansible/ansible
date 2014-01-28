# $FreeBSD$

PORTNAME=       ansible
PORTVERSION=    1.0
PORTREVISION=   1
CATEGORIES=     python net-mgmt
MASTER_SITES=   http://releases.ansible.com/ansible/
DISTNAME=		${PORTNAME}-${PORTVERSION}

MAINTAINER=		briancoca+ansible@gmail.com
COMMENT=        Ansible ssh based config management framework

RUN_DEPENDS=   python>2.5:${PORTSDIR}/lang/python ${PORTSDIR}/devel/py-Jinja2 ${PORTSDIR}/devel/py-yaml \
				${PORTSDIR}/security/py-paramiko ${PORTSDIR}/devel/py-simplejson

FETCH_ARGS=	-pRr

USE_PYTHON=     yes
USE_PYDISTUTILS=	yes

#TODO:add optional dependencies (fireball mode i.e)

# extracts with github name + short hash, needs to be updated with new releases
#pre-configure:
#	@${MV} ${WRKDIR}/ansible ${WRKSRC}

.include <bsd.port.mk>
