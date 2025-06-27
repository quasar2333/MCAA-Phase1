import argparse
import time
import planner
import coder
import executor
import memory_manager
from config import DEFAULT_PROVIDER, DEFAULT_MODEL


def run_agent(goal: str, provider_name: str = DEFAULT_PROVIDER, model_id: str | None = None, log_func=print):
    """Run the agent once with the given goal."""
    log = log_func
    log("=== MCAA-Phase1 Agent ===")

    plan = planner.create_plan(goal, provider_name, model_id)
    if not plan:
        log("无法为该目标创建计划")
        return

    log("生成的计划:")
    for step in plan:
        log(f"  步骤 {step['step_number']}: {step['task']} - {step['details']}")

    error_counts: dict[str, int] = {}

    for step in plan:
        log(f"\n--- 执行步骤 {step['step_number']}:{step['task']} ---")
        task_type = step['task']
        details = step['details']
        script_code = ""
        tool_name = ""

        if task_type == "USE_EXISTING_TOOL":
            tool_name = details
            tools = memory_manager.load_tools()
            found_tool = next((t for t in tools if t['name'] == tool_name), None)
            if found_tool:
                log(f"找到现有工具: {tool_name}")
                script_code = found_tool['code']
            else:
                log(f"未找到工具: {tool_name}, 跳过")
                continue
        elif task_type == "CREATE_NEW_TOOL":
            script_code = coder.create_code(details, provider_name, model_id)
            if not script_code or "Traceback" in script_code:
                log(f"生成代码失败: {script_code}")
                error_counts[script_code] = error_counts.get(script_code, 0) + 1
                if error_counts[script_code] >= 3:
                    log("同样的错误出现三次，任务终止")
                    return
                continue
        else:
            log(f"未知的任务类型: {task_type}")
            continue

        script_name = f"{tool_name or 'temp'}_{int(time.time())}.py"
        success, output = executor.run_script(script_code, script_name)
        log(output)

        if success and task_type == "CREATE_NEW_TOOL":
            save_name = f"{tool_name or 'tool'}_{int(time.time())}"
            memory_manager.save_tool(save_name, details, script_code, log)
        if not success:
            error_counts[output] = error_counts.get(output, 0) + 1
            if error_counts[output] >= 3:
                log("同样的错误出现三次，任务终止")
                return

    log("任务完成！")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the MCAA agent")
    parser.add_argument("--provider", default=DEFAULT_PROVIDER, help="provider name")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="model id (optional)")
    parser.add_argument("goal", nargs='?', default="", help="goal for the agent")
    args = parser.parse_args()

    if args.goal:
        run_agent(args.goal, args.provider, args.model)
    else:
        while True:
            try:
                g = input("\n请输入任务目标(或exit退出): ")
                if g.lower() == 'exit':
                    break
                run_agent(g, args.provider, args.model)
            except KeyboardInterrupt:
                break

