import os
import urllib.request
from urllib.error import HTTPError, URLError

# 1. 保存目录
save_dir = os.path.join("assets", "icons")
os.makedirs(save_dir, exist_ok=True)

# 2. 穷举目前技术圈绝大多数常见关键词 (覆盖语言、框架、云原生、工具等)
candidates = [
    # 编程语言
    "cpp", "c", "csharp", "java", "python", "js", "ts", "go", "rust", 
    "php", "ruby", "swift", "kotlin", "dart", "scala", "elixir", "haskell",
    # 前端框架与移动端
    "react", "vue", "angular", "svelte", "nextjs", "nuxtjs", "flutter", 
    "html5", "css3", "sass", "less", "tailwindcss", "bootstrap", "redux",
    # 后端与环境
    "nodejs", "express", "nest", "spring", "django", "flask", "fastapi", 
    "rails", "laravel", "graphql", "restapi",
    # 构建、测试与工具
    "webpack", "vite", "babel", "jest", "cypress", "eslint", "prettier", 
    "npm", "yarn", "pnpm", "git", "github", "gitlab", "linux", "nginx",
    # 数据库与 DevOps
    "mysql", "postgresql", "mongodb", "redis", "sqlite", "docker", 
    "kubernetes", "aws", "azure", "gcp", "firebase", "supabase",
    # AI 与其它
    "tensorflow", "pytorch", "pandas", "numpy", "figma", "postman"
]

print(f"📦 开始全量扫描并下载，候选库共 {len(candidates)} 个技术关键词...\n")

success_count = 0
skip_count = 0

for icon in candidates:
    url = f"https://techstack-generator.vercel.app/{icon}-icon.svg"
    file_path = os.path.join(save_dir, f"{icon}.svg")
    
    # 如果本地已经有了，直接跳过（方便以后重复跑命令补全）
    if os.path.exists(file_path):
        print(f"⏭️  跳过 (已存在): {icon}.svg")
        success_count += 1
        continue

    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            content = response.read()
            # 校验 content 是否真正包含 SVG 标签，防止存入 404 HTML 页面
            if b"<svg" in content:
                with open(file_path, "wb") as f:
                    f.write(content)
                print(f"✅ 下载成功: {icon}.svg")
                success_count += 1
            else:
                skip_count += 1
                # 默默跳过服务端不认识的图标
    except (HTTPError, URLError):
        skip_count += 1

print(f"\n🎉 囤货完毕！成功获取并校验 {success_count} 个带动画 SVG！(跳过了 {skip_count} 个该节点未收录的词)")
print(f"📁 所有图标已妥善保存在: {os.path.abspath(save_dir)}")