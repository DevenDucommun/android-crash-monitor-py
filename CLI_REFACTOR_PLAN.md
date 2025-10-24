# CLI Refactoring Plan

## Current State
- **File**: `cli.py` (663 lines)
- **Commands**: 8 commands in one file
- **Issues**: Mixed concerns, hard to test, difficult to extend

## Commands to Extract

1. `setup` - Run interactive setup wizard (lines ~102-143)
2. `start` - One-command setup and monitoring (lines ~145-251)
3. `monitor` - Start monitoring (lines ~252-323)
4. `devices` - List connected devices (lines ~324-355)
5. `logs` - Show/export logs (lines ~356-469)
6. `config` - Configuration management (lines ~470-513)
7. `analyze` - Analyze crashes (lines ~514-608)
8. `gui` - Launch GUI (lines ~609-663)

## Target Structure

```
cli/
├── __init__.py              (~50 lines) - Main CLI group, exports
├── main.py                  (~100 lines) - CLI entry point with group setup
├── commands/
│   ├── __init__.py          (~20 lines) - Command exports
│   ├── setup_cmd.py         (~60 lines) - Setup wizard command
│   ├── start_cmd.py         (~120 lines) - Start command
│   ├── monitor_cmd.py       (~90 lines) - Monitor command
│   ├── devices_cmd.py       (~50 lines) - Devices command
│   ├── logs_cmd.py          (~130 lines) - Logs command
│   ├── config_cmd.py        (~60 lines) - Config command
│   ├── analyze_cmd.py       (~110 lines) - Analyze command
│   └── gui_cmd.py           (~70 lines) - GUI command
└── utils/
    ├── __init__.py          (~10 lines)
    ├── formatters.py        (~80 lines) - Output formatting
    └── helpers.py           (~50 lines) - Common CLI helpers
```

## Benefits

### Maintainability
- Each command in its own file (~50-130 lines)
- Clear separation of concerns
- Easy to locate and fix issues

### Testability
- Each command can be tested independently
- Mock click context easily
- Unit test command logic separately

### Extensibility
- Add new commands without touching existing code
- Easy to add command-specific options
- Better command documentation

## Refactoring Steps

1. ✅ Create directory structure
2. ⏭️ Extract shared utilities (formatters, helpers)
3. ⏭️ Extract each command to its own module
4. ⏭️ Create new main.py that imports commands
5. ⏭️ Update cli.py to re-export from new structure (backward compat)
6. ⏭️ Add tests for each command
7. ⏭️ Verify all commands work
8. ⏭️ Eventually replace old cli.py

## Backward Compatibility

Keep `cli.py` as a facade that imports from new structure:
```python
from .cli.main import cli
__all__ = ['cli']
```

This ensures existing code continues to work while we refactor.

## Success Criteria

- [ ] All 8 commands extracted
- [ ] Each command file <150 lines
- [ ] Backward compatible imports
- [ ] All commands tested
- [ ] Documentation updated
- [ ] CLI works identically to before

---

**Status**: Planning Complete
**Next**: Extract utilities and first command
