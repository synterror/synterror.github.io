import sys
import click
from builder import config as blog_config
from builder import site as blog_site
from builder import post as blog_post


@click.group()
@click.option('--config', type=click.Path(exists=True, readable=True), default=blog_config.DEFAULT_CFG_PATH)
@click.pass_context
def main(ctx, config):
    ctx.ensure_object(dict)
    ctx.obj['config'] = blog_config.load(config)


@main.group()
def post():
    pass


@post.command('create')
@click.option('--date', type=click.STRING, default=None)
@click.option('--tags', type=click.STRING, default='')
@click.option('--slug', type=click.STRING, default='')
@click.pass_context
def post_create(ctx, date, tags, slug):
    config = ctx.obj['config']

    blog_post.create_post(config, date, slug, tags)


@main.group()
def site():
    pass


@site.command('generate')
@click.option('--force/-f', default=False)
@click.pass_context
def site_generate(ctx, force):
    blog_site.generate(ctx.obj['config'], force)


if __name__ == '__main__':
    main(sys.argv[1:])
