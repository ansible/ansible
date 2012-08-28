# $FreeBSD$

PORTNAME=       ansible
PORTVERSION=    0.6
CATEGORIES=     devel www textproc python
MASTER_SITES=   https://github.com/downloads/ansible/ansible/

MAINTAINER=		briancoca+ansible@gmail.com
COMMENT=        Ansible ssh based config management framework

RUN_DEPENDS=   python>2.5:${PORTSDIR}/lang/python ${PORTSDIR}/devel/py-Jinja2 ${PORTSDIR}/devel/py-yaml \
				${PORTSDIR}/security/py-paramiko ${PORTSDIR}/devel/py-simplejson

FETCH_ARGS=	-pRr

USE_PYTHON=	yes
USE_PYDISTUTILS=	yes

# extracts with github name + short hash, needs to be updated with new releases
#pre-configure:
#	@${MV} ${WRKDIR}/ansible ${WRKSRC}

.include <bsd.port.mk>
