import glob
from pathlib import Path
import os
from urllib.parse import urljoin, urlparse
import click
from jinja2 import Environment, FileSystemLoader
import markdown2 as md
from . import config


def generate(config, force):
    folders = config.get('folders', {})
    output_path = folders.get('site', 'site')
    posts_path = folders.get('posts', 'posts')
    templates_path = folders.get('templates', 'templates')
    template_name = config.get('template', 'light')
    templates_path = Path(templates_path) / template_name
    posts_path = Path(posts_path)
    output_path = Path(output_path)

    if not templates_path.exists() or not templates_path.is_dir():
        raise ValueError(
            'Templates path does not exist or is not a folder', templates_path)

    if not posts_path.exists() or not posts_path.is_dir():
        raise ValueError(
            'Posts path does not exist or is not a folder', posts_path)

    if output_path.exists():
        if not output_path.is_dir():
            raise ValueError('Output path is not a folder', output_path)
    else:
        output_path.mkdir(parents=True, exist_ok=True)

    template_engine = Environment(
        loader=FileSystemLoader(templates_path),
        trim_blocks=True,
        lstrip_blocks=True
    )

    get_template = lambda name: template_engine.get_template(name + '.jinja')

    # Render main pages
    click.echo('Rendering main pages...')
    generate_main(config, get_template, posts_path, output_path)

    click.echo('Rendering posts...')
    generate_posts(config, get_template, posts_path, output_path, force)


def generate_main(config, get_template, posts_path, output_path):
    read_previews_args = [posts_path, output_path]

    if 'post-preview-count' in config:
        read_previews_args.append(config['post-preview-count'])

    if 'post-preview-length' in config:
        read_previews_args.append(config['post-preview-length'])

    metadata = read_previews(*read_previews_args)
    context = make_context(config, meta=metadata)

    render_to_file(
        context,
        get_template('index'),
        output_path / 'index.html'
    )


def generate_posts(config, get_template, posts_path, output_path, force=False):
    posts = posts_path.glob('**/*.yml')

    for p in posts:
        generate_single_post(config, get_template, p, output_path, force)


def make_context(config, **extra_content):
    return {
        'config': config,
        'urljoin': urljoin,
        'blogurl': lambda rel_url: urljoin(config.get('home', '/'), rel_url),
        **extra_content
    }


def generate_single_post(config, get_template, post_path: Path, output_path, force=False):
    meta = read_single_post_metadata(post_path)
    title, subtitle, body = read_post_text(post_path.with_suffix('.md'))
    output_post_folder = output_path / 'posts' / str(meta['date'].year)
    slug = meta.get('slug')
    output_post_path = output_post_folder / \
        '{}.html'.format(slug or post_path.stem)

    output_post_folder.mkdir(mode=0o755, parents=True, exist_ok=True)

    if output_post_path.exists() and not force:
        return

    body = md.markdown(body)
    context = make_context(
        config,
        meta=meta,
        post={
            'title': title,
            'subtitle': subtitle,
            'body': body
        }
    )

    render_to_file(
        context,
        get_template('post'),
        output_post_path
    )


def render(context, template):
    return template.render(**context)


def render_to_file(context, template, output_path):
    rendered_doc = render(context, template)

    with open(output_path, 'w') as f:
        f.write(rendered_doc)


def read_posts_metadata(paths):
    meta = {}

    for p in paths:
        meta[p] = read_single_post_metadata(p)

    return meta


def read_single_post_metadata(path: Path):
    return config.read_yaml(path)


def read_previews(posts_path, output_path, preview_count=5, preview_length=100):
    previews = list(find_previews(posts_path, preview_count))
    text_paths = list(map(lambda p: p.with_suffix('.md'), previews))
    meta = read_posts_metadata(previews)
    texts = read_posts_text(text_paths, preview_length)
    res = {}

    for p, t in zip(previews, text_paths):
        post_meta = meta[p]
        prev_key = Path('posts') / str(post_meta['date'].year)

        if post_meta.get('slug'):
            prev_key /= '{}.html'.format(post_meta['slug'])
        else:
            prev_key /= '{}.html'.format(p.stem)

        prev_key = str(prev_key).replace(os.path.sep, '/')
        prev_data = {
            **texts[t],
            **meta[p],
            'id': p.stem
        }

        res[prev_key] = prev_data

    return res


def read_posts_text(paths, max_body_length=None):
    texts = {}

    for p in paths:
        title, subtitle, body = read_post_text(p)
        body_short = body[:max_body_length]

        if len(body_short) < len(body):
            body_short += '...'

        body_short = md.markdown(body_short)

        texts[p] = {
            'title': title,
            'subtitle': subtitle,
            'body': body_short
        }

    return texts


def find_previews(posts_path: Path, preview_count):
    meta_paths = posts_path.glob('**/*.yml')
    meta_info = []

    for p in meta_paths:
        meta_info.append({
            'path': p,
            'last_modified': p.stat().st_mtime
        })

    return map(
        lambda info: Path(info['path']),
        sorted(meta_info, key=lambda m: m['last_modified'], reverse=True)[
            :preview_count]
    )


def read_post_text(post_path):
    with open(post_path, 'r') as f:
        text = f.read()

    lines = text.splitlines(keepends=True)
    title = None
    subtitle = ''

    if lines[0].startswith('# '):
        title = lines[0][1:].strip()
        lines = lines[1:]

        if lines[0].startswith('## '):
            subtitle = lines[0][2:].strip()
            lines = lines[1:]

    text_no_title = (''.join(lines)).strip()

    if not title:
        raise ValueError('Post has no title', post_path)

    return title, subtitle, text_no_title
