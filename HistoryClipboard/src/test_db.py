"""
数据层验证脚本 — 测试所有 CRUD 操作
用法：python src/test_db.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from database import init_db, add_item, get_items, toggle_pin, delete_item
from database import cleanup_expired, get_total_count, get_last_hash


def test():
    # 清理旧数据库，确保每次测试独立
    from utils import get_db_path, get_data_dir
    db_path = get_db_path()
    if os.path.exists(db_path):
        os.remove(db_path)
        # 清理可能的 WAL 文件
        for ext in ["-wal", "-shm"]:
            wal = db_path + ext
            if os.path.exists(wal):
                os.remove(wal)
        print(f"  -> 已清理旧数据库")

    print(f"  -> 数据目录: {get_data_dir()}")

    print("=" * 50)
    print("测试 1: 初始化数据库")
    init_db()
    print("  -> 建表成功")

    print("\n测试 2: 新增文字记录")
    id1 = add_item("text", "这是第一条测试文字", content_hash="hash_001")
    id2 = add_item("text", "第二条文字内容Hello World", content_hash="hash_002")
    id3 = add_item("text", "又一条测试记录", content_hash="hash_003")
    print(f"  -> 新增 3 条，ID: {id1}, {id2}, {id3}")

    print("\n测试 3: 新增图片记录")
    id4 = add_item("image", image_path="/tmp/test.png",
                   thumbnail_path="/tmp/test_thumb.png", content_hash="hash_img")
    print(f"  -> 新增图片记录，ID: {id4}")

    print("\n测试 4: 获取所有记录（应有4条，按时间倒序）")
    items = get_items()
    for it in items:
        print(f"  id={it['id']} type={it['type']} pinned={it['pinned']} "
              f"content={str(it['content'])[:30]}")
    assert len(items) == 4, f"期望4条，实际{len(items)}条"

    print("\n测试 5: 获取最新 hash（去重用）")
    last_hash = get_last_hash()
    print(f"  -> last_hash = {last_hash}")
    assert last_hash == "hash_img"

    print("\n测试 6: 置顶操作")
    result = toggle_pin(id2)
    print(f"  -> 置顶 id={id2}，新状态: {result}")
    items = get_items()
    pinned_ids = [it["id"] for it in items if it["pinned"]]
    print(f"  -> 置顶项 IDs: {pinned_ids}")
    assert id2 in pinned_ids, "id2 应该已被置顶"
    assert items[0]["id"] == id2, "置顶项应该在第一位"

    print("\n测试 7: 取消置顶")
    result = toggle_pin(id2)
    print(f"  -> 取消置顶 id={id2}，新状态: {result}")
    assert result is False

    print("\n测试 8: 搜索功能")
    items = get_items(search="Hello")
    print(f"  -> 搜索 'Hello' 结果数: {len(items)}")
    assert len(items) >= 1
    # 搜出来的第一条可能是图片(content=None)，找文字记录验证
    text_items = [it for it in items if it["type"] == "text"]
    assert len(text_items) >= 1
    assert "Hello" in text_items[0]["content"]

    items = get_items(search="不存在的内容XYZ")
    print(f"  -> 搜索 '不存在的内容XYZ' 结果数: {len(items)}（仅图片，无匹配文字）")
    # 无匹配文字时仍返回图片记录，文字记录应为0
    text_match = [it for it in items if it["type"] == "text"]
    assert len(text_match) == 0

    print("\n测试 9: 删除记录")
    info = delete_item(id1)
    print(f"  -> 删除 id={id1}: content={str(info['content'])[:20]}")
    assert info is not None
    assert get_total_count() == 3

    print("\n测试 10: 过期清理（retention_days=0 → 清理所有非置顶）")
    # 先置顶一条，验证不会被清理
    toggle_pin(id3)
    deleted = cleanup_expired(retention_days=0)
    print(f"  -> 过期清理删除了 {len(deleted)} 条")
    remaining = get_items()
    print(f"  -> 剩余记录: {len(remaining)}")
    assert len(remaining) == 1, f"置顶项应保留，实际剩余{len(remaining)}"
    assert remaining[0]["id"] == id3

    print("\n" + "=" * 50)
    print("全部测试通过!")
    print("=" * 50)


if __name__ == "__main__":
    test()
