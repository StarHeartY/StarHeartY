import os
import urllib.request

save_dir = os.path.join("assets", "icons")
os.makedirs(save_dir, exist_ok=True)

# 为每个图标量身定制专属 @keyframes 和 CSS 类
custom_animations = {
    "vite": {
        "api": "vite",
        "css": """
          @keyframes lightningHop {
            0%, 100% { transform: translateY(0px) scale(1); }
            15% { transform: translateY(-7px) scale(1.08, 0.95); }
            30% { transform: translateY(0px) scale(0.98, 1.02); }
            45% { transform: translateY(-3px) scale(1.03); }
            60% { transform: translateY(0px) scale(1); }
          }
          .custom-anim { animation: lightningHop 2.2s cubic-bezier(0.28, 0.84, 0.42, 1) infinite; transform-origin: center bottom; }
        """
    },
    "html": {
        "api": "html",
        "css": """
          @keyframes shieldRock {
            0%, 100% { transform: rotate(0deg); }
            25% { transform: rotate(-8deg); }
            75% { transform: rotate(8deg); }
          }
          .custom-anim { animation: shieldRock 3.5s ease-in-out infinite; transform-origin: center bottom; }
        """
    },
    "css": {
        "api": "css",
        "css": """
          @keyframes shieldFlip {
            0%, 100% { transform: perspective(200px) rotateY(0deg); }
            50% { transform: perspective(200px) rotateY(22deg) scale(1.04); }
          }
          .custom-anim { animation: shieldFlip 3s ease-in-out infinite; transform-origin: center; }
        """
    },
    "git": {
        "api": "git",
        "css": """
          @keyframes branchSwing {
            0%, 100% { transform: rotate(-10deg); }
            50% { transform: rotate(12deg); }
          }
          .custom-anim { animation: branchSwing 2.8s ease-in-out infinite; transform-origin: center center; }
        """
    },
    "nodejs": {
        "api": "nodejs",
        "css": """
          @keyframes hexaPulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.11); }
          }
          .custom-anim { animation: hexaPulse 2.4s ease-in-out infinite; transform-origin: center center; }
        """
    },
    "vscode": {
        "api": "vscode",
        "css": """
          @keyframes codeDrift {
            0%, 100% { transform: translateY(0px) rotate(0deg); }
            50% { transform: translateY(-6px) rotate(5deg); }
          }
          .custom-anim { animation: codeDrift 3.2s ease-in-out infinite; transform-origin: center; }
        """
    }
}

print("🎨 开始为 6 个缺失的图标量身打造「专属定制动画」...\n")

for name, config in custom_animations.items():
    url = f"https://skillicons.dev/icons?i={config['api']}"
    file_path = os.path.join(save_dir, f"{name}.svg")
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            svg_content = response.read().decode('utf-8')
            first_tag_end = svg_content.find('>') + 1
            
            header = svg_content[:first_tag_end].replace('<svg ', '<svg overflow="visible" ')
            body = svg_content[first_tag_end:].replace('</svg>', '')
            
            style_tag = f"<style>{config['css']}</style>\n<g class=\"custom-anim\">"
            final_svg = f"{header}{style_tag}{body}</g></svg>"
            
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(final_svg)
            print(f"✨ 成功打造专属特效 [{name}.svg]")
            
    except Exception as e:
        print(f"❌ 下载失败 ({name}): {e}")

print("\n🎉 大功告成！现在赶快在预览里看看，不再是千篇一律的上下浮动了！")