from __future__ import annotations

from ansible.module_utils.embed import EmbedManager

e1 = EmbedManager.embed('.', 'embed_this.py')
e2 = EmbedManager.embed('.', 'embed_that.py')
