# -*- coding: utf-8 -*-

# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

import re

SU_PROMPT_LOCALIZATIONS = [
    'Password',
    '암호',
    'パスワード',
    'Adgangskode',
    'Contraseña',
    'Contrasenya',
    'Hasło',
    'Heslo',
    'Jelszó',
    'Lösenord',
    'Mật khẩu',
    'Mot de passe',
    'Parola',
    'Parool',
    'Pasahitza',
    'Passord',
    'Passwort',
    'Salasana',
    'Sandi',
    'Senha',
    'Wachtwoord',
    'ססמה',
    'Лозинка',
    'Парола',
    'Пароль',
    'गुप्तशब्द',
    'शब्दकूट',
    'సంకేతపదము',
    'හස්පදය',
    '密码',
    '密碼',
]

SU_PROMPT_LOCALIZATIONS_RE = re.compile("|".join(['(\w+\'s )?' + x + ' ?: ?' for x in SU_PROMPT_LOCALIZATIONS]), flags=re.IGNORECASE)

def check_su_prompt(data):
    return bool(SU_PROMPT_LOCALIZATIONS_RE.match(data))

