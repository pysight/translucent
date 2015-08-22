export default function defer(times, func) {
    let called = 0;
    let funcArgs = null;

    return args => {
        called += 1;
        funcArgs = funcArgs || args;
        if (called === times) {
            return func(funcArgs);
        }
    };
}
