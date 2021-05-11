frappe.provide("erpnext.bloombrackets");

const { CMD_CALL } = require('./bloombrackets/constants');
const { CommandInsert, ExpressionInsert } = require('./bloombrackets/inserters');
const { 
  CustomCommand, 
  Input, 
  Block, 
  Variable, 
  IfThenElse, 
  Expression, 
  ComparisonOperatorSelector, 
  VarSet, 
  MathExp 
} = require('./bloombrackets/renderers');

class BloomBracketsComponent {
  constructor($wrapper, frm, script_field) {
    this.$wrapper = $wrapper;
    this.frm = frm;

    // Redefines components here to avoid cyclical dependency.
    // UI Inserters
    this.insertExpressionInsert = ExpressionInsert.bind(null, this);
    this.insertCommandInsert = CommandInsert.bind(null, this);

    // Commands UI
    this.insertVariable = Variable.bind(null, this);
    this.insertIfThenElse = IfThenElse.bind(null, this);
    this.insertBlock = Block.bind(null, this);
    this.insertExpression = Expression.bind(null, this);
    this.insertComparisonOperatorSelector = ComparisonOperatorSelector.bind(null, this);
    this.insertInput = Input.bind(null, this);
    this.insertVarSet = VarSet.bind(null, this);
    this.insertCustomCommand = CustomCommand.bind(null, this);
    this.insertMathExp = MathExp.bind(null, this);

    // Default script to kickoff UI:
    this.script = [];
    this.context = {};

    this.script_field = script_field;
    this.id_count = 0;
    if (frm.doc[this.script_field]) {
      try {
        this.script = JSON.parse(frm.doc[this.script_field]);
        console.dir(this.script);
      } catch (err) {
        console.error(err);
      }
    }

    this.make();
  }

  make() {
    return frappe.run_serially([
      () => frappe.dom.freeze(),
      () => this.load_meta(),
			() => this.build_editor(),
			() => frappe.dom.unfreeze()
		]);
  }

  async load_meta() {
    const meta = await this.frm.call("get_brackets_meta");
    this.context = meta.message;
  }

  build_editor() {
    const html = Block(this, { block: this.script, cls: 'bb-block-top' });
    //const html = this.render_block(this.script);

    this.$wrapper.closest('.frappe-control').removeAttr('title');
    this.$wrapper.empty().append(html);
    this.$wrapper.trigger('bb-init');

    this.$wrapper.on('bb-script-change', () => {
      if ( this.script ) {
        const script = JSON.stringify(this.script);
        this.frm.set_value(this.script_field, script);
      }
    })
  }

  list_vars() {
    return Object.keys(this.context['#VARMETA'] || {});
  }
}

erpnext.bloombrackets.Component = BloomBracketsComponent;
module.exports.BloomBracketsComponent = BloomBracketsComponent;