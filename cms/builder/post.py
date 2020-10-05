from datetime import date
from pathlib import Path
from uuid import uuid4 as uuid
from .config import write_yaml


def create_post(config, post_date, slug, tags):
    post_id = str(uuid())
    folders = config.get('folders', {})
    posts_path = Path(folders.get('posts', 'posts'))
    post_date = post_date or date.today()
    tags = tags.split(',')
    new_post_meta_path = posts_path / str(post_date.year) / '{}.yml'.format(post_id)
    new_post_content_path: Path = new_post_meta_path.with_suffix('.md')

    meta = {
        'slug': slug,
        'date': post_date,
        'tags': tags
    }

    if new_post_content_path.exists() or new_post_meta_path.exists():
        raise RuntimeError('Possible ID collision', post_id)

    write_yaml(new_post_meta_path, meta)

    with new_post_content_path.open('w') as f:
        pass
