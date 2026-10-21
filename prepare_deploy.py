import os
import shutil

def prepare():
    print("=== GoMobile: Preparing Assets for Netlify Production Deployment ===")
    base_dir = os.path.dirname(os.path.abspath(__file__))
    public_dir = os.path.join(base_dir, 'public')
    public_static = os.path.join(public_dir, 'static')
    
    # 1. Ensure public/static directory exists
    os.makedirs(public_static, exist_ok=True)
    
    # 2. Copy static files into public/static
    src_static = os.path.join(base_dir, 'static')
    if os.path.exists(src_static):
        shutil.copytree(src_static, public_static, dirs_exist_ok=True)
        print("-> Static assets successfully synchronized to public/static/")

    # 3. Create _redirects fallback in public/
    redirects_path = os.path.join(public_dir, '_redirects')
    with open(redirects_path, 'w', encoding='utf-8') as f:
        f.write("# Netlify redirects for GoMobile\n")
        f.write("/static/*   /static/:splat           200\n")
        f.write("/*          /.netlify/functions/app  200\n")
    print("-> Generated public/_redirects fallback rule.")

    print("=== Build preparation completed successfully! ===")

if __name__ == '__main__':
    prepare()
