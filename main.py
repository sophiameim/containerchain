import os
from quart import Quart, jsonify
from spiders.containerchain_empty_depot_inquiry import main as containerchain_empty_depot_inquiry_main


app = Quart(__name__)

@app.route("/run-containerchainemptydepotinquiry", methods=['POST']) #改口令
async def run_containerchain_empty_depot_inquiry_main_endpoint(): #改函数名
    try:
        message_start = "containerchain_empty_depot_inquiry spider started!" #改信号名
        print(message_start)
        await containerchain_empty_depot_inquiry_main()  # 改主函数名
        message_end = "containerchain_empty_depot_inquiry spider finished!" #改信号名
        print(message_end)
        return jsonify({"message": message_end}), 200
    except Exception as e:
        print(f"Error in run_containerchain_empty_depot_inquiry_main_endpoint: {e}") #改信号名
        return jsonify({"message": f"Error: {e}"}), 500


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
