import { Component } from "../component";

export const Input = Component("bb-control", (ui, $container, {
  exp, autofocus, reference_exp, onDelete, onChange, onRef, exp_meta
}) => {
  let $input = $container.find('input');
  const handleReferenceChange = (ref) => {
  }

  if ( reference_exp ) {
    handleReferenceChange(reference_exp);
  }

  const handleValueChange = (e) => {
    exp[1] = $(e.target).val();
    if ( onChange ) {
      onChange(exp);
    }

    ui.$wrapper.trigger('bb-script-change');
  }

  $container.find('.bb-control').on('bb-change', (e, cexp, meta, side) => {
    if ( cexp != exp && side ) {
      handleReferenceChange(cexp, meta);
    }
  });

  const value = Array.isArray(exp)?exp[1]:exp;
  let link_input = null;
  if ( exp_meta ) {
    if ( exp_meta.fieldtype == "Link" ) {
      $container.empty();
      link_input = frappe.ui.form.make_control({
        df: Object.assign({
          "fieldname": exp_meta.name,
          get_status: () => 'Write'
        }, exp_meta),
        parent: $container,
        horizontal: true
      });
      link_input.make_wrapper();
      link_input.make_input();
      link_input.toggle_description(false);
      $input = link_input.$input;
    } 

    if ( exp_meta.description ) {
      $input.attr("title", exp_meta.description);
    }
  }

  $input.on('blur', handleValueChange);

  if ( value ) {
    if ( link_input ) {
      link_input.set_data_value(value, value);
    } else {
      $input.val(value);
    }
  }    

  if ( autofocus ) {
    $input.focus();
  }

}, () => `<input type="text" />`
);