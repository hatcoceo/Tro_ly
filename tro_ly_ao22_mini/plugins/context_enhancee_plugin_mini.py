import logging


def register(assistant):
    assistant.context['config'] = {'language': 'vi', 'debug': True}
    logger = logging.getLogger('VirtualAssistant')
    logger.setLevel(logging.DEBUG if assistant.context['config']['debug'] else
        logging.INFO)
    handler = logging.StreamHandler()
    formatter = logging.Formatter('[%(levelname)s] %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    assistant.context['logger'] = logger
    logger.info('Logger đã sẵn sàng.')
    assistant.context['services'] = {}

    def emit_event(name, data=None):
        logger.debug(f'Emit event: {name}')
        bus = assistant.context.get('event_bus')
        if bus:
            bus.emit(name, data)
    assistant.context['emit_event'] = emit_event
    assistant.context['assistant'] = assistant
    logger.info('✅ Context Enhancer đã khởi tạo thành công.')


plugin_info = {'enabled': False, 'register': register, 'command_handle': []}
