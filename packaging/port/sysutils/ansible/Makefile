# $FreeBSD$

PORTNAME=	ansible
PORTVERSION=	2.1
PORTREVISION=	1
CATEGORIES=	python net-mgmt sysutils
MASTER_SITES=	http://releases.ansible.com/ansible/
DISTNAME=	${PORTNAME}-${PORTVERSION}

MAINTAINER=	bcoca@ansible.com
COMMENT=	Ansible ssh based config management framework

LICENSE=	GPLv3
LICENSE_FILE=	${WRKSRC}/COPYING

RUN_DEPENDS=	python>2.5:${PORTSDIR}/lang/python \
               ${PORTSDIR}/devel/py-Jinja2 \
               ${PORTSDIR}/devel/py-yaml \
               ${PORTSDIR}/security/py-paramiko \
               ${PORTSDIR}/devel/py-simplejson \
               ${PORTSDIR}/security/py-pycrypto

OPTIONS_DEFINE=	EXAMPLES

FETCH_ARGS=	-pRr

USE_PYTHON=	yes
USE_PYDISTUTILS=	yes

CPE_VENDOR=	Ansible Inc

SUB_FILES=	pkg-message

PLIST_FILES+=	man/man1/ansible-doc.1.gz \
                man/man1/ansible-galaxy.1.gz \
                man/man1/ansible-playbook.1.gz \
                man/man1/ansible-pull.1.gz \
                man/man1/ansible-vault.1.gz \
                man/man1/ansible.1.gz

PORTEXAMPLES=	ansible.cfg hosts

post-patch:
.for f in bin/ansible-galaxy docs/man/man1/ansible-galaxy.1 \
        docs/man/man1/ansible-playbook.1 docs/man/man1/ansible.1 \
        examples/ansible.cfg examples/hosts lib/ansible/constants.py \
        lib/ansible/module_utils/urls.py lib/ansible/modules/core/system/setup.py \
        lib/ansible/playbook/__init__.py lib/ansible/runner/__init__.py
        @${REINPLACE_CMD} -e 's|/etc/ansible|${ETCDIR}|' ${WRKSRC}/${f}
.endfor

.for f in docs/man/man1/ansible-playbook.1 docs/man/man1/ansible.1 \
        examples/ansible.cfg lib/ansible/constants.py \
        lib/ansible/playbook/__init__.py lib/ansible/runner/__init__.py \
        @${REINPLACE_CMD} -e 's|/usr/share/ansible|${DATADIR}|' ${WRKSRC}/${f}
.endfor

post-install:
				@${MKDIR} ${STAGEDIR}${MAN1PREFIX}/man/man1
				${INSTALL_MAN} ${WRKSRC}/docs/man/man1/*.1 \
            ${STAGEDIR}${MAN1PREFIX}/man/man1
				@${MKDIR} ${STAGEDIR}${EXAMPLESDIR}
				${INSTALL_DATA} ${WRKSRC}/examples/ansible.cfg ${STAGEDIR}${EXAMPLESDIR}
				${INSTALL_DATA} ${WRKSRC}/examples/hosts ${STAGEDIR}${EXAMPLESDIR}

.include <bsd.port.mk>
